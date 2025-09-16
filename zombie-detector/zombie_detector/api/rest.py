# zombie_detector/api/rest.py
# filepath: zombie-detector/zombie_detector/api/rest.py
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import tempfile
import json
import os
from zombie_detector import process_zombies
from ..core.processor import (
    filter_zombies,
    get_zombie_summary,
    get_killed_zombies_summary,
)
from ..core.zombie_tracker import ZombieTracker
from ..core.classifier import ALIAS_BY_CODE  # Import the real aliases
from ..utils.utils import validate_host_data


# Pydantic models for request/response validation
class HostData(BaseModel):
    dynatrace_host_id: str
    hostname: str
    Recent_CPU_decrease_criterion: int
    Recent_net_traffic_decrease_criterion: int
    Sustained_Low_CPU_criterion: int
    Excessively_constant_RAM_criterion: int
    Daily_CPU_profile_lost_criterion: int
    # Optional fields
    report_date: Optional[str] = None
    tenant: Optional[str] = None
    asset_tag: Optional[str] = None
    pending_decommission: Optional[str] = None
    Recent_CPU_decrease_value: Optional[Any] = None
    Recent_net_traffic_decrease_value: Optional[Any] = None
    Sustained_Low_CPU_value: Optional[Any] = None
    Excessively_constant_RAM_value: Optional[Any] = None
    Daily_CPU_profile_lost_value: Optional[Any] = None


class DetectionOptions(BaseModel):
    zombies_only: bool = Field(
        default=False, description="Return only hosts classified as zombies"
    )
    include_summary: bool = Field(
        default=False, description="Include summary statistics in response"
    )


class DetectionRequest(BaseModel):
    hosts: List[Dict[str, Any]]
    states: Optional[Dict[str, int]] = Field(
        default=None, description="Criterion states configuration"
    )
    options: Optional[DetectionOptions] = Field(default_factory=DetectionOptions)


class DetectionResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]
    summary: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "0.1.0"


class StatesResponse(BaseModel):
    states: Dict[str, int]


class CriteriaResponse(BaseModel):
    criteria: Dict[str, Dict[str, str]]


class KilledZombiesResponse(BaseModel):
    killed_zombies_count: int
    since_hours: int
    killed_zombies: List[Dict[str, Any]]
    criterion_breakdown: Dict[str, int]


class ZombieLifecycleResponse(BaseModel):
    zombie_id: str
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_detections: int
    is_active: bool
    killed_info: Optional[Dict[str, Any]] = None
    detection_history: List[Dict[str, Any]]


class TrackingStatsResponse(BaseModel):
    new_zombies: List[str]
    persisting_zombies: List[str]
    killed_zombies: List[str]
    stats: Dict[str, int]


app = FastAPI(
    title="Zombie Host Detector API",
    description="API for detecting zombie hosts based on performance criteria",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.post("/api/v1/zombie-detection", response_model=DetectionResponse)
async def detect_zombies(request: DetectionRequest):
    """
    Detect zombie hosts based on performance criteria.

    - **hosts**: List of host data objects with performance metrics
    - **states**: Optional criterion states configuration (0=inactive, 1=active)
    - **options**: Detection options (zombies_only, include_summary)
    """
    try:
        hosts = request.hosts
        states = request.states or {}
        options = request.options or DetectionOptions()

        if not hosts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No hosts data provided"
            )

        # Validate hosts data
        invalid_hosts = []
        for i, host in enumerate(hosts):
            if not validate_host_data(host):
                invalid_hosts.append(i)

        if invalid_hosts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid host data",
                    "invalid_host_indices": invalid_hosts,
                    "required_fields": [
                        "dynatrace_host_id",
                        "hostname",
                        "Recent_CPU_decrease_criterion",
                        "Recent_net_traffic_decrease_criterion",
                        "Sustained_Low_CPU_criterion",
                        "Excessively_constant_RAM_criterion",
                        "Daily_CPU_profile_lost_criterion",
                    ],
                },
            )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as hosts_file:
            json.dump(hosts, hosts_file)
            hosts_file_path = hosts_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as states_file:
            # FIXED: Use the real criterion codes from your classifier
            default_states = {
                "0": 0,  # No zombie
                "1A": 1,
                "1B": 1,
                "1C": 1,
                "1D": 1,
                "1E": 1,  # Single criteria
                "2A": 1,
                "2B": 1,
                "2C": 1,
                "2D": 1,
                "2E": 1,  # Double criteria
                "2F": 1,
                "2G": 1,
                "2H": 1,
                "2I": 1,
                "2J": 1,
                "3A": 1,
                "3B": 1,
                "3C": 1,
                "3D": 1,
                "3E": 1,  # Triple criteria
                "3F": 1,
                "3G": 1,
                "3H": 1,
                "3I": 1,
                "3J": 1,
                "4A": 1,
                "4B": 1,
                "4C": 1,
                "4D": 1,
                "4E": 1,  # Quadruple criteria
                "5": 1,  # All five criteria
            }

            final_states = {**default_states, **states}
            json.dump(final_states, states_file)
            states_file_path = states_file.name

        try:
            results = process_zombies(hosts_file_path, states_file_path)

            if options.zombies_only:
                results = filter_zombies(results)

            response_data = {"status": "success", "results": results}

            if options.include_summary:
                response_data["summary"] = get_zombie_summary(results)

            return DetectionResponse(**response_data)

        finally:
            # Clean up temporary files
            os.unlink(hosts_file_path)
            os.unlink(states_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="zombie-detector")


@app.get("/api/v1/states", response_model=StatesResponse)
async def get_default_states():
    """Get default criterion states configuration."""
    # FIXED: Return the real criterion codes
    default_states = {
        "0": 0,  # No zombie detected
        "1A": 1,
        "1B": 1,
        "1C": 1,
        "1D": 1,
        "1E": 1,  # Single criteria zombies
        "2A": 1,
        "2B": 1,
        "2C": 1,
        "2D": 1,
        "2E": 1,  # Double criteria zombies
        "2F": 1,
        "2G": 1,
        "2H": 1,
        "2I": 1,
        "2J": 1,
        "3A": 1,
        "3B": 1,
        "3C": 1,
        "3D": 1,
        "3E": 1,  # Triple criteria zombies
        "3F": 1,
        "3G": 1,
        "3H": 1,
        "3I": 1,
        "3J": 1,
        "4A": 1,
        "4B": 1,
        "4C": 1,
        "4D": 1,
        "4E": 1,  # Quadruple criteria zombies
        "5": 1,  # All five criteria active
    }
    return StatesResponse(states=default_states)


@app.get("/api/v1/criteria", response_model=CriteriaResponse)
async def get_criteria_info():
    """Get information about zombie detection criteria."""
    # FIXED: Use the real aliases and provide better descriptions
    criteria_descriptions = {
        "0": "No zombie criteria detected - host is operating normally",
        # Single criteria descriptions
        "1A": "Recent CPU decrease detected",
        "1B": "Recent network traffic decrease detected",
        "1C": "Sustained low CPU usage detected",
        "1D": "Excessively constant RAM usage detected",
        "1E": "Daily CPU profile pattern lost",
        # Double criteria descriptions
        "2A": "Recent CPU and network traffic decrease detected (Ghoul pattern)",
        "2B": "Recent CPU decrease and sustained low CPU detected",
        "2C": "Recent CPU decrease and constant RAM detected",
        "2D": "Recent CPU decrease and lost daily CPU profile detected",
        "2E": "Recent network decrease and sustained low CPU detected",
        "2F": "Recent network decrease and constant RAM detected",
        "2G": "Recent network decrease and lost daily CPU profile detected",
        "2H": "Sustained low CPU and constant RAM detected",
        "2I": "Sustained low CPU and lost daily CPU profile detected",
        "2J": "Constant RAM and lost daily CPU profile detected",
        # Triple criteria descriptions
        "3A": "CPU decline, network decline, and low CPU pattern detected",
        "3B": "CPU decline, network decline, and constant RAM detected",
        "3C": "CPU decline, network decline, and lost CPU profile detected",
        "3D": "CPU decline, low CPU, and constant RAM detected",
        "3E": "CPU decline, low CPU, and lost CPU profile detected",
        "3F": "CPU decline, constant RAM, and lost CPU profile detected",
        "3G": "Network decline, low CPU, and constant RAM detected",
        "3H": "Network decline, low CPU, and lost CPU profile detected",
        "3I": "Network decline, constant RAM, and lost CPU profile detected",
        "3J": "Low CPU, constant RAM, and lost CPU profile detected",
        # Quadruple criteria descriptions
        "4A": "All criteria except recent CPU decrease detected",
        "4B": "All criteria except recent network decrease detected",
        "4C": "All criteria except sustained low CPU detected",
        "4D": "All criteria except constant RAM detected",
        "4E": "All criteria except lost daily CPU profile detected",
        # All five criteria
        "5": "All five zombie criteria detected - critical zombie state",
    }

    criteria_info = {}
    for criterion_code, alias in ALIAS_BY_CODE.items():
        criteria_info[criterion_code] = {
            "alias": alias,
            "description": criteria_descriptions.get(
                criterion_code, f"Zombie criterion {criterion_code}"
            ),
        }

    return CriteriaResponse(criteria=criteria_info)


@app.get("/api/v1/zombies/killed", response_model=KilledZombiesResponse)
async def get_killed_zombies(
    since_hours: int = Query(
        24, description="Hours to look back for killed zombies", ge=1, le=168
    ),
):
    """
    Get zombies that were killed (resolved) in the specified time period.

    - **since_hours**: Hours to look back (1-168, default: 24)
    """
    try:
        summary = get_killed_zombies_summary(since_hours)
        return KilledZombiesResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving killed zombies: {str(e)}",
        )


@app.get("/api/v1/zombies/{zombie_id}/killed", response_model=Dict[str, Any])
async def check_zombie_killed(zombie_id: str):
    """
    Check if a specific zombie was killed (resolved).

    - **zombie_id**: Dynatrace host ID to check
    """
    try:
        tracker = ZombieTracker()
        killed_info = tracker.is_zombie_killed(zombie_id)

        if killed_info:
            return {
                "is_killed": True,
                "zombie_id": zombie_id,
                "killed_info": killed_info,
            }
        else:
            return {"is_killed": False, "zombie_id": zombie_id, "killed_info": None}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking zombie status: {str(e)}",
        )


@app.get(
    "/api/v1/zombies/{zombie_id}/lifecycle", response_model=ZombieLifecycleResponse
)
async def get_zombie_lifecycle(zombie_id: str):
    """
    Get the complete lifecycle information for a specific zombie.

    - **zombie_id**: Dynatrace host ID to get lifecycle for
    """
    try:
        tracker = ZombieTracker()
        lifecycle = tracker.get_zombie_lifecycle(zombie_id)

        if not lifecycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No lifecycle data found for zombie {zombie_id}",
            )

        return ZombieLifecycleResponse(**lifecycle)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving zombie lifecycle: {str(e)}",
        )


@app.get("/api/v1/zombies/tracking-stats", response_model=TrackingStatsResponse)
async def get_tracking_stats():
    """
    Get current zombie tracking statistics (new, persisting, killed).
    """
    try:
        # This would typically come from the last tracking operation
        # For now, return empty stats - you might want to store this differently
        return TrackingStatsResponse(
            new_zombies=[],
            persisting_zombies=[],
            killed_zombies=[],
            stats={
                "total_zombies": 0,
                "new_zombies": 0,
                "persisting_zombies": 0,
                "killed_zombies": 0,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tracking stats: {str(e)}",
        )


@app.post("/api/v1/zombies/cleanup")
async def cleanup_zombie_data(
    days_to_keep: int = Query(30, description="Days of data to keep", ge=1, le=365),
):
    """
    Clean up old zombie tracking data.

    - **days_to_keep**: Number of days of data to keep (1-365, default: 30)
    """
    try:
        tracker = ZombieTracker()
        tracker.cleanup_old_data(days_to_keep)
        return {"message": f"Cleaned up zombie data older than {days_to_keep} days"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up data: {str(e)}",
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Zombie Host Detector API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "description": "Advanced zombie detection with Spanish creature classification system",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
