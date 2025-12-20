"""
Google Business Profile Reviews Service
Fetches and caches reviews from Google Places API
Compliant with Google's Terms of Service
"""

import requests
from django.conf import settings
from django.core.cache import cache
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache duration: 24 hours (in seconds)
REVIEW_CACHE_DURATION = 60 * 60 * 24
REVIEW_CACHE_KEY = 'google_business_reviews'


class GoogleReviewsService:
    """
    Service to fetch and manage Google Business Profile reviews.
    Uses caching to minimize API calls and costs.
    """
    
    def __init__(self):
        # Use server API key (without HTTP referer restrictions) for backend calls
        self.api_key = getattr(settings, 'GOOGLE_SERVER_API_KEY', None) or getattr(settings, 'GOOGLE_PLACES_API_KEY', None)
        self.place_id = getattr(settings, 'GOOGLE_PLACE_ID', 'ChIJgfA7KTUDYzkR6n9gjeGDYoI')
        self.base_url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    def get_reviews(self, force_refresh=False):
        """
        Get Google reviews with caching.
        Returns cached data if available, otherwise fetches fresh data.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            dict: Contains business_name, rating, total_reviews, reviews list, and metadata
        """
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = cache.get(REVIEW_CACHE_KEY)
            if cached_data:
                logger.info("Returning cached Google reviews")
                cached_data['from_cache'] = True
                return cached_data
        
        # Fetch fresh data from API
        fresh_data = self._fetch_from_api()
        
        if fresh_data and fresh_data.get('success'):
            # Store in cache for 24 hours
            cache.set(REVIEW_CACHE_KEY, fresh_data, REVIEW_CACHE_DURATION)
            fresh_data['from_cache'] = False
            logger.info(f"Cached {len(fresh_data.get('reviews', []))} Google reviews for 24 hours")
        
        return fresh_data
    
    def _fetch_from_api(self):
        """
        Fetch reviews directly from Google Places API.
        
        Returns:
            dict: Parsed review data or error information
        """
        if not self.api_key:
            logger.error("Google Places API Key is not configured")
            return {
                'success': False,
                'error': 'API key not configured',
                'error_code': 'API_KEY_MISSING'
            }
        
        # Build API request
        params = {
            'place_id': self.place_id,
            'fields': 'name,rating,user_ratings_total,reviews',
            'key': self.api_key
        }
        
        try:
            print(f"[GoogleReviews] Fetching reviews for place_id: {self.place_id}")
            print(f"[GoogleReviews] API URL: {self.base_url}")
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            print(f"[GoogleReviews] HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"[GoogleReviews] HTTP Error: {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP Error: {response.status_code}',
                    'error_code': 'HTTP_ERROR'
                }
            
            data = response.json()
            
            # Check API response status
            status = data.get('status')
            print(f"[GoogleReviews] API Status: {status}")
            
            if status != 'OK':
                error_message = data.get('error_message', 'Unknown error')
                print(f"[GoogleReviews] API Error: {status} - {error_message}")
                return {
                    'success': False,
                    'error': error_message,
                    'error_code': status
                }
            
            # Parse the response
            result = data.get('result', {})
            reviews_data = result.get('reviews', [])
            
            # Format reviews (read-only, no modifications to text)
            formatted_reviews = []
            for review in reviews_data:
                formatted_reviews.append({
                    'author_name': review.get('author_name', 'Anonymous'),
                    'author_url': review.get('author_url', ''),
                    'profile_photo_url': review.get('profile_photo_url', ''),
                    'rating': review.get('rating', 0),
                    'text': review.get('text', ''),  # Exact text, no modifications
                    'time': review.get('time', 0),
                    'relative_time_description': review.get('relative_time_description', ''),
                })
            
            return {
                'success': True,
                'business_name': result.get('name', 'SS Electricals'),
                'rating': result.get('rating', 0),
                'total_reviews': result.get('user_ratings_total', 0),
                'reviews': formatted_reviews,
                'fetched_at': datetime.now().isoformat(),
                'place_id': self.place_id
            }
            
        except requests.exceptions.Timeout:
            logger.error("Google API request timed out")
            return {
                'success': False,
                'error': 'Request timed out',
                'error_code': 'TIMEOUT'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Google API request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUEST_FAILED'
            }
        except Exception as e:
            logger.error(f"Unexpected error fetching Google reviews: {e}")
            return {
                'success': False,
                'error': 'An unexpected error occurred',
                'error_code': 'UNKNOWN_ERROR'
            }
    
    def clear_cache(self):
        """Clear the cached reviews data."""
        cache.delete(REVIEW_CACHE_KEY)
        logger.info("Google reviews cache cleared")
    
    def get_cache_status(self):
        """Get information about the current cache status."""
        cached_data = cache.get(REVIEW_CACHE_KEY)
        if cached_data:
            return {
                'cached': True,
                'fetched_at': cached_data.get('fetched_at'),
                'review_count': len(cached_data.get('reviews', [])),
                'rating': cached_data.get('rating')
            }
        return {'cached': False}


# Singleton instance
google_reviews_service = GoogleReviewsService()


def get_google_reviews(force_refresh=False):
    """
    Convenience function to get Google reviews.
    
    Args:
        force_refresh: If True, bypass cache
        
    Returns:
        dict: Review data
    """
    return google_reviews_service.get_reviews(force_refresh=force_refresh)
