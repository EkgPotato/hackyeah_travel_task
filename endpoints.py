from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import sqlite3
import json
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="City Travel Metrics API",
    description="API for accessing travel metrics for European cities",
    version="1.0.0"
)


origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Pozwól na wszystkie metody HTTP (GET, POST, PUT, DELETE itp.)
    allow_headers=["*"],  # Pozwól na wszystkie nagłówki w żądaniach
)


# Pydantic Models
class MetricDetail(BaseModel):
    score: float = Field(..., ge=0, le=10, description="Score from 0 to 10")
    description: str = Field(..., description="Detailed assessment")
    tips: str = Field(..., description="Practical tips for travelers")
    recommendations: List[str] = Field(..., description="Specific recommendations")


class CityMetrics(BaseModel):
    id: int
    country: str
    capital: str
    analysis_date: str

    # Overview
    city_description: str
    overall_summary: str

    # Metrics
    safety: MetricDetail
    sustainability: MetricDetail
    enjoyment: MetricDetail
    calmcation: MetricDetail
    cultural_exchange: MetricDetail
    navigation: MetricDetail
    eco_friendly: MetricDetail

    # Overall
    overall_score: float = Field(..., ge=0, le=10)
    best_features: str
    improvement_areas: str

    # Stats
    post_count: int
    total_engagement: int


class CityList(BaseModel):
    cities: List[dict]
    total_count: int


class ScoresSummary(BaseModel):
    capital: str
    country: str
    overall_score: float
    safety_score: float
    sustainability_score: float
    enjoyment_score: float
    calmcation_score: float
    cultural_exchange_score: float
    navigation_score: float
    eco_friendly_score: float


# Database connection helper
def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect('travel_metrics.db')
    conn.row_factory = sqlite3.Row
    return conn


def parse_recommendations(value):
    """Parse recommendations from database (could be JSON string or plain text)."""
    if not value:
        return []
    try:
        # Try to parse as JSON
        recommendations = json.loads(value)
        if isinstance(recommendations, list):
            return recommendations
        return [str(recommendations)]
    except:
        # If not JSON, split by common delimiters
        if ',' in value:
            return [r.strip() for r in value.split(',')]
        elif '\n' in value:
            return [r.strip() for r in value.split('\n') if r.strip()]
        return [value]


@app.get("/", tags=["Root"])
def read_root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to City Travel Metrics API",
        "endpoints": {
            "GET /cities": "List all available cities",
            "GET /city/{city_name}": "Get metrics for a specific city",
            "GET /city/{city_name}/scores": "Get only scores for a city",
            "GET /top-cities": "Get top cities by overall score",
            "GET /top-cities/{category}": "Get top cities by specific category"
        },
        "categories": [
            "safety", "sustainability", "enjoyment", "calmcation",
            "cultural_exchange", "navigation", "eco_friendly"
        ]
    }


@app.get("/cities", response_model=CityList, tags=["Cities"])
def get_all_cities():
    """Get a list of all cities in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT capital, country, overall_score, analysis_date
        FROM city_metrics
        ORDER BY capital
    ''')

    cities = cursor.fetchall()
    conn.close()

    if not cities:
        raise HTTPException(status_code=404, detail="No cities found in database")

    cities_list = [
        {
            "capital": city['capital'],
            "country": city['country'],
            "overall_score": city['overall_score'],
            "analysis_date": city['analysis_date']
        }
        for city in cities
    ]

    return {
        "cities": cities_list,
        "total_count": len(cities_list)
    }


@app.get("/city/{city_name}", response_model=CityMetrics, tags=["Cities"])
def get_city_metrics(
        city_name: str,
        country: Optional[str] = Query(None, description="Filter by country if multiple cities have the same name")
):
    """Get comprehensive travel metrics for a specific city."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if country:
        cursor.execute('''
            SELECT * FROM city_metrics
            WHERE LOWER(capital) = LOWER(?)
            AND LOWER(country) = LOWER(?)
        ''', (city_name, country))
    else:
        cursor.execute('''
            SELECT * FROM city_metrics
            WHERE LOWER(capital) = LOWER(?)
        ''', (city_name,))

    city = cursor.fetchone()
    conn.close()

    if not city:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_name}' not found in database"
        )

    # Build response
    return CityMetrics(
        id=city['id'],
        country=city['country'],
        capital=city['capital'],
        analysis_date=city['analysis_date'],
        city_description=city['city_description'],
        overall_summary=city['overall_summary'],

        safety=MetricDetail(
            score=city['safety_score'],
            description=city['safety_description'],
            tips=city['safety_tips'],
            recommendations=parse_recommendations(city['safety_recommendations'])
        ),

        sustainability=MetricDetail(
            score=city['sustainability_score'],
            description=city['sustainability_description'],
            tips=city['sustainability_tips'],
            recommendations=parse_recommendations(city['sustainability_recommendations'])
        ),

        enjoyment=MetricDetail(
            score=city['enjoyment_score'],
            description=city['enjoyment_description'],
            tips=city['enjoyment_tips'],
            recommendations=parse_recommendations(city['enjoyment_recommendations'])
        ),

        calmcation=MetricDetail(
            score=city['calmcation_score'],
            description=city['calmcation_description'],
            tips=city['calmcation_tips'],
            recommendations=parse_recommendations(city['calmcation_recommendations'])
        ),

        cultural_exchange=MetricDetail(
            score=city['cultural_exchange_score'],
            description=city['cultural_exchange_description'],
            tips=city['cultural_exchange_tips'],
            recommendations=parse_recommendations(city['cultural_exchange_recommendations'])
        ),

        navigation=MetricDetail(
            score=city['navigation_score'],
            description=city['navigation_description'],
            tips=city['navigation_tips'],
            recommendations=parse_recommendations(city['navigation_recommendations'])
        ),

        eco_friendly=MetricDetail(
            score=city['eco_friendly_score'],
            description=city['eco_friendly_description'],
            tips=city['eco_friendly_tips'],
            recommendations=parse_recommendations(city['eco_friendly_recommendations'])
        ),

        overall_score=city['overall_score'],
        best_features=city['best_features'],
        improvement_areas=city['improvement_areas'],
        post_count=city['post_count'],
        total_engagement=city['total_engagement']
    )


@app.get("/city/{city_name}/scores", response_model=ScoresSummary, tags=["Cities"])
def get_city_scores(
        city_name: str,
        country: Optional[str] = Query(None, description="Filter by country")
):
    """Get only the scores for a specific city (lightweight response)."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if country:
        cursor.execute('''
            SELECT capital, country, overall_score, safety_score, sustainability_score,
                   enjoyment_score, calmcation_score, cultural_exchange_score,
                   navigation_score, eco_friendly_score
            FROM city_metrics
            WHERE LOWER(capital) = LOWER(?)
            AND LOWER(country) = LOWER(?)
        ''', (city_name, country))
    else:
        cursor.execute('''
            SELECT capital, country, overall_score, safety_score, sustainability_score,
                   enjoyment_score, calmcation_score, cultural_exchange_score,
                   navigation_score, eco_friendly_score
            FROM city_metrics
            WHERE LOWER(capital) = LOWER(?)
        ''', (city_name,))

    city = cursor.fetchone()
    conn.close()

    if not city:
        raise HTTPException(
            status_code=404,
            detail=f"City '{city_name}' not found in database"
        )

    return ScoresSummary(
        capital=city['capital'],
        country=city['country'],
        overall_score=city['overall_score'],
        safety_score=city['safety_score'],
        sustainability_score=city['sustainability_score'],
        enjoyment_score=city['enjoyment_score'],
        calmcation_score=city['calmcation_score'],
        cultural_exchange_score=city['cultural_exchange_score'],
        navigation_score=city['navigation_score'],
        eco_friendly_score=city['eco_friendly_score']
    )


@app.get("/top-cities", tags=["Rankings"])
def get_top_cities(
        limit: int = Query(10, ge=1, le=50, description="Number of top cities to return")
):
    """Get top cities by overall score."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT capital, country, overall_score, safety_score, sustainability_score,
               enjoyment_score, calmcation_score, cultural_exchange_score,
               navigation_score, eco_friendly_score, city_description
        FROM city_metrics
        ORDER BY overall_score DESC
        LIMIT ?
    ''', (limit,))

    cities = cursor.fetchall()
    conn.close()

    if not cities:
        raise HTTPException(status_code=404, detail="No cities found")

    return [
        {
            "rank": idx,
            "capital": city['capital'],
            "country": city['country'],
            "overall_score": city['overall_score'],
            "scores": {
                "safety": city['safety_score'],
                "sustainability": city['sustainability_score'],
                "enjoyment": city['enjoyment_score'],
                "calmcation": city['calmcation_score'],
                "cultural_exchange": city['cultural_exchange_score'],
                "navigation": city['navigation_score'],
                "eco_friendly": city['eco_friendly_score']
            },
            "description": city['city_description']
        }
        for idx, city in enumerate(cities, 1)
    ]


@app.get("/top-cities/{category}", tags=["Rankings"])
def get_top_cities_by_category(
        category: str,
        limit: int = Query(10, ge=1, le=50, description="Number of top cities to return")
):
    """Get top cities by specific category (safety, sustainability, enjoyment, etc.)."""

    valid_categories = {
        "safety": "safety_score",
        "sustainability": "sustainability_score",
        "enjoyment": "enjoyment_score",
        "calmcation": "calmcation_score",
        "cultural_exchange": "cultural_exchange_score",
        "navigation": "navigation_score",
        "eco_friendly": "eco_friendly_score"
    }

    if category.lower() not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Valid categories: {list(valid_categories.keys())}"
        )

    score_column = valid_categories[category.lower()]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f'''
        SELECT capital, country, {score_column} as category_score,
               overall_score, city_description
        FROM city_metrics
        ORDER BY {score_column} DESC
        LIMIT ?
    ''', (limit,))

    cities = cursor.fetchall()
    conn.close()

    if not cities:
        raise HTTPException(status_code=404, detail="No cities found")

    return {
        "category": category,
        "top_cities": [
            {
                "rank": idx,
                "capital": city['capital'],
                "country": city['country'],
                "category_score": city['category_score'],
                "overall_score": city['overall_score'],
                "description": city['city_description']
            }
            for idx, city in enumerate(cities, 1)
        ]
    }


@app.get("/search", tags=["Search"])
def search_cities(
        query: str = Query(..., min_length=2, description="Search term for city or country"),
        limit: int = Query(10, ge=1, le=50)
):
    """Search for cities by name or country."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT capital, country, overall_score, city_description
        FROM city_metrics
        WHERE LOWER(capital) LIKE LOWER(?)
        OR LOWER(country) LIKE LOWER(?)
        ORDER BY overall_score DESC
        LIMIT ?
    ''', (f'%{query}%', f'%{query}%', limit))

    cities = cursor.fetchall()
    conn.close()

    if not cities:
        raise HTTPException(
            status_code=404,
            detail=f"No cities found matching '{query}'"
        )

    return [
        {
            "capital": city['capital'],
            "country": city['country'],
            "overall_score": city['overall_score'],
            "description": city['city_description']
        }
        for city in cities
    ]


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Check if the API and database are working."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM city_metrics')
        result = cursor.fetchone()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "cities_in_database": result['count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
