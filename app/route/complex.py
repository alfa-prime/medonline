from typing import Dict, Any
import asyncio
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.params import Body

from app.core.logger import logger
from app.models.patient import PatientSearchRequest
from app.core.dependencies import get_valid_cookies_dependency

from app.services.ultrasound_scan import pipeline as ultrasound_scan_pipeline
from app.services.functional_tests import pipeline as functional_tests_pipeline
from app.services.medtest import pipeline as medtest_pipeline
from app.services.x_ray import pipeline as x_ray_pipeline

router = APIRouter(prefix="/complex", tags=["Complex results"])


@router.post("/person", openapi_extra={"requestBody": {"description": "Patient tests search request body"}})
async def get_tests(request: PatientSearchRequest = Body(
    ...,
    example={
        "last_name": "Богачев",
        "first_name": "Константин",
        "middle_name": "Юрьевич",
        "birthday": "16.01.1982",
    },
),
    cookies: Dict = Depends(get_valid_cookies_dependency)
) -> Dict[str, Any]:

    try:
        logger.info(f"Fetching all tests for patient ...")
        results = await asyncio.gather(
            functional_tests_pipeline.get_patient_tests(
                cookies, request.last_name, request.first_name, request.middle_name, request.birthday
            ),
            ultrasound_scan_pipeline.get_patient_tests(
                cookies, request.last_name, request.first_name, request.middle_name, request.birthday
            ),
            medtest_pipeline.get_patient_tests(
                cookies, request.last_name, request.first_name, request.middle_name, request.birthday
            ),
            x_ray_pipeline.get_patient_tests(
                cookies, request.last_name, request.first_name, request.middle_name, request.birthday
            ),
            return_exceptions=True
        )
        logger.info(f"All tests for patient fetched.")

        (functional_tests_result, ultrasound_scan_result, medtest_result, x_ray_result) = results

        all_results = [x_ray_result, medtest_result, ultrasound_scan_result, functional_tests_result]

        # Логируем ошибки, если они были
        for i, res in enumerate(all_results):
            if isinstance(res, Exception):
                logger.error(f"A sub-request failed during complex fetch: {res}", exc_info=res)
                all_results[i] = None  # Заменяем ошибку на None для ответа клиенту

        if not any(r for r in all_results if r is not None):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results could be fetched for this patient."
            )

        # Извлекаем информацию о пациенте (она одинаковая во всех результатах)
        person = None
        for result in all_results:
            if result and "person" in result:
                person = result.pop("person")
                break

        # Убираем дублирующуюся информацию о пациенте из остальных результатов
        for result in all_results:
            if result:
                result.pop("person", None)

        return {
            "success": True,
            "result": {
                "person": person,
                "medtests": all_results[1],
                "ultrasound_scan": all_results[2],
                "functional_tests": all_results[3],
                "x_ray": all_results[0],
            }
        }

    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"An error occurred while processing the request: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
