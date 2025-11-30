"""Routes for DogeAnalyze dashboard."""

from flask import jsonify, render_template, request
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from database.models import MarketData, AnalysisResult, ScriptStatus, get_db_session
from utils.logger import setup_logger

logger = setup_logger('dashboard.routes')


def register_routes(app):
    """Register all routes with the Flask app."""
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        return render_template('index.html')
    
    @app.route('/api/health')
    def health():
        """Health check endpoint."""
        try:
            db = get_db_session()
            # Test database connection with a simple query
            db.query(func.count(MarketData.id)).scalar()
            db.close()
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @app.route('/api/current')
    def get_current():
        """Get current market data (latest entry)."""
        try:
            db = get_db_session()
            latest = db.query(MarketData).order_by(desc(MarketData.timestamp)).first()
            
            if not latest:
                db.close()
                return jsonify({
                    'error': 'No market data available'
                }), 404
            
            result = latest.to_dict()
            db.close()
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Error fetching current data: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/history')
    def get_history():
        """Get historical market data."""
        try:
            hours = request.args.get('hours', default=24, type=int)
            limit = request.args.get('limit', default=100, type=int)
            
            db = get_db_session()
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            data = db.query(MarketData).filter(
                MarketData.timestamp >= cutoff_time
            ).order_by(MarketData.timestamp).limit(limit).all()
            
            result = [item.to_dict() for item in data]
            db.close()
            
            return jsonify({
                'data': result,
                'count': len(result),
                'hours': hours
            }), 200
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/analysis')
    def get_analysis():
        """Get analysis results."""
        try:
            timeframe = request.args.get('timeframe', default=None, type=str)
            
            db = get_db_session()
            query = db.query(AnalysisResult)
            
            if timeframe:
                query = query.filter(AnalysisResult.timeframe == timeframe)
            
            # Get latest analysis for each timeframe
            results = query.order_by(desc(AnalysisResult.timestamp)).all()
            
            # Group by timeframe and get latest
            analysis_by_timeframe = {}
            for result in results:
                if result.timeframe not in analysis_by_timeframe:
                    analysis_by_timeframe[result.timeframe] = result.to_dict()
            
            db.close()
            
            return jsonify({
                'data': list(analysis_by_timeframe.values()),
                'by_timeframe': analysis_by_timeframe
            }), 200
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/status')
    def get_status():
        """Get script statuses."""
        try:
            db = get_db_session()
            statuses = db.query(ScriptStatus).all()
            
            result = [status.to_dict() for status in statuses]
            db.close()
            
            return jsonify({
                'data': result,
                'count': len(result)
            }), 200
        except Exception as e:
            logger.error(f"Error fetching status: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/stats')
    def get_stats():
        """Get dashboard statistics."""
        try:
            db = get_db_session()
            
            # Get latest price
            latest = db.query(MarketData).order_by(desc(MarketData.timestamp)).first()
            
            # Get price change (24h ago vs now)
            day_ago = datetime.utcnow() - timedelta(hours=24)
            old_price = db.query(MarketData).filter(
                MarketData.timestamp <= day_ago
            ).order_by(desc(MarketData.timestamp)).first()
            
            # Count total records
            total_records = db.query(func.count(MarketData.id)).scalar()
            
            # Get latest analysis count
            analysis_count = db.query(func.count(AnalysisResult.id)).scalar()
            
            stats = {
                'current_price': float(latest.price_usd) if latest else None,
                'price_change_24h': None,
                'total_data_points': total_records,
                'total_analyses': analysis_count,
                'last_update': latest.timestamp.isoformat() if latest else None
            }
            
            if latest and old_price:
                price_change = ((float(latest.price_usd) - float(old_price.price_usd)) / float(old_price.price_usd)) * 100
                stats['price_change_24h'] = round(price_change, 2)
            
            db.close()
            return jsonify(stats), 200
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return jsonify({
                'error': str(e)
            }), 500

