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
        """Get latest analysis results (one per timeframe)."""
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
            
            # Get all available timeframes from database
            all_timeframes = db.query(AnalysisResult.timeframe).distinct().all()
            available_timeframes = [tf[0] for tf in all_timeframes]
            
            db.close()
            
            return jsonify({
                'data': list(analysis_by_timeframe.values()),
                'by_timeframe': analysis_by_timeframe,
                'available_timeframes': available_timeframes
            }), 200
        except Exception as e:
            logger.error(f"Error fetching analysis: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/analysis/history')
    def get_analysis_history():
        """Get historical analysis results (prediction history)."""
        try:
            timeframe = request.args.get('timeframe', default=None, type=str)
            limit = request.args.get('limit', default=100, type=int)
            hours = request.args.get('hours', default=None, type=int)
            
            # Limit max results to prevent huge responses
            limit = min(limit, 1000)
            
            db = get_db_session()
            query = db.query(AnalysisResult)
            
            # Filter by timeframe if provided
            if timeframe:
                query = query.filter(AnalysisResult.timeframe == timeframe)
            
            # Filter by time range if provided
            if hours:
                cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                query = query.filter(AnalysisResult.timestamp >= cutoff_time)
            
            # Order by timestamp descending (most recent first)
            results = query.order_by(desc(AnalysisResult.timestamp)).limit(limit).all()
            
            data = [result.to_dict() for result in results]
            db.close()
            
            # Group by timeframe for summary
            by_timeframe = {}
            for result in results:
                tf = result.timeframe
                if tf not in by_timeframe:
                    by_timeframe[tf] = []
                by_timeframe[tf].append(result.to_dict())
            
            return jsonify({
                'data': data,
                'count': len(data),
                'by_timeframe': by_timeframe,
                'timeframe': timeframe,
                'limit': limit,
                'hours': hours
            }), 200
        except Exception as e:
            logger.error(f"Error fetching analysis history: {e}")
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
    
    @app.route('/api/accuracy')
    def get_accuracy():
        """Get prediction accuracy data by comparing predicted vs actual prices."""
        try:
            timeframe = request.args.get('timeframe', default=None, type=str)
            limit = request.args.get('limit', default=50, type=int)
            
            db = get_db_session()
            
            # Get predictions
            query = db.query(AnalysisResult).filter(
                AnalysisResult.predicted_price.isnot(None)
            ).order_by(desc(AnalysisResult.timestamp))
            
            if timeframe:
                query = query.filter(AnalysisResult.timeframe == timeframe)
            
            predictions = query.limit(limit).all()
            
            accuracy_data = []
            
            for pred in predictions:
                # Calculate when this prediction should be validated
                # Handle minute-based timeframes (e.g., '10m', '15m')
                if pred.timeframe.endswith('m'):
                    minutes = int(pred.timeframe[:-1])
                    timeframe_hours = minutes / 60.0
                elif pred.timeframe.endswith('h'):
                    timeframe_hours = int(pred.timeframe[:-1])
                elif pred.timeframe.endswith('d'):
                    days = int(pred.timeframe[:-1])
                    timeframe_hours = days * 24
                else:
                    timeframe_hours = 24  # Default fallback
                
                validation_time = pred.timestamp + timedelta(hours=timeframe_hours)
                
                # Get actual price at validation time (or closest available)
                # Find the closest market data point to validation time
                # For minute-based timeframes, use a smaller window
                window_hours = 1.0 if timeframe_hours >= 1.0 else timeframe_hours
                candidates = db.query(MarketData).filter(
                    MarketData.timestamp >= validation_time - timedelta(hours=window_hours),
                    MarketData.timestamp <= validation_time + timedelta(hours=window_hours)
                ).all()
                
                actual_price_query = None
                if candidates:
                    # Find the closest one by timestamp difference
                    min_diff = None
                    for candidate in candidates:
                        diff = abs((candidate.timestamp - validation_time).total_seconds())
                        if min_diff is None or diff < min_diff:
                            min_diff = diff
                            actual_price_query = candidate
                
                if actual_price_query and pred.predicted_price:
                    predicted = float(pred.predicted_price)
                    actual = float(actual_price_query.price_usd)
                    
                    # Calculate accuracy percentage
                    if actual > 0:
                        error_percentage = abs((predicted - actual) / actual) * 100
                        accuracy = max(0, 100 - error_percentage)
                        
                        # Determine if prediction was correct (within 5% error)
                        is_correct = error_percentage <= 5.0
                        
                        accuracy_data.append({
                            'timestamp': pred.timestamp.isoformat(),
                            'timeframe': pred.timeframe,
                            'predicted_price': predicted,
                            'actual_price': actual,
                            'accuracy': round(accuracy, 2),
                            'error_percentage': round(error_percentage, 2),
                            'is_correct': is_correct,
                            'validation_time': validation_time.isoformat()
                        })
            
            db.close()
            
            # Calculate overall statistics
            if accuracy_data:
                avg_accuracy = sum(d['accuracy'] for d in accuracy_data) / len(accuracy_data)
                correct_count = sum(1 for d in accuracy_data if d['is_correct'])
                total_count = len(accuracy_data)
                
                stats = {
                    'average_accuracy': round(avg_accuracy, 2),
                    'correct_predictions': correct_count,
                    'total_predictions': total_count,
                    'success_rate': round((correct_count / total_count) * 100, 2) if total_count > 0 else 0
                }
            else:
                stats = {
                    'average_accuracy': 0,
                    'correct_predictions': 0,
                    'total_predictions': 0,
                    'success_rate': 0
                }
            
            return jsonify({
                'data': accuracy_data,
                'stats': stats
            }), 200
        except Exception as e:
            logger.error(f"Error fetching accuracy: {e}")
            return jsonify({
                'error': str(e)
            }), 500
    
    @app.route('/api/analysis/timeline')
    def get_analysis_timeline():
        """Get analysis timeline showing when analyses were performed and actual prices at validation time."""
        try:
            timeframe = request.args.get('timeframe', default=None, type=str)
            limit = request.args.get('limit', default=100, type=int)
            
            db = get_db_session()
            query = db.query(AnalysisResult).order_by(desc(AnalysisResult.timestamp))
            
            if timeframe:
                query = query.filter(AnalysisResult.timeframe == timeframe)
            
            results = query.limit(limit).all()
            
            # Group by timeframe and get timeline with validation data
            timeline_data = {}
            for result in results:
                tf = result.timeframe
                if tf not in timeline_data:
                    timeline_data[tf] = []
                
                # Initialize validation variables
                validation_time = None
                actual_price = None
                actual_price_time = None
                accuracy = None
                error_percentage = None
                is_validated = False
                
                # Calculate validation time (when prediction should come true)
                if result.timestamp and result.predicted_price:
                    # Calculate timeframe in hours
                    if tf.endswith('m'):
                        minutes = int(tf[:-1])
                        timeframe_hours = minutes / 60.0
                    elif tf.endswith('h'):
                        timeframe_hours = int(tf[:-1])
                    elif tf.endswith('d'):
                        timeframe_hours = int(tf[:-1]) * 24
                    else:
                        timeframe_hours = 24
                    
                    validation_time = result.timestamp + timedelta(hours=timeframe_hours)
                    
                    # Get actual price at validation time (or closest available)
                    candidates = db.query(MarketData).filter(
                        MarketData.timestamp >= validation_time - timedelta(hours=1),
                        MarketData.timestamp <= validation_time + timedelta(hours=1)
                    ).all()
                    
                    if candidates:
                        # Find the closest one by timestamp difference
                        min_diff = None
                        for candidate in candidates:
                            diff = abs((candidate.timestamp - validation_time).total_seconds())
                            if min_diff is None or diff < min_diff:
                                min_diff = diff
                                actual_price = float(candidate.price_usd)
                                actual_price_time = candidate.timestamp.isoformat()
                    
                    # Calculate accuracy if we have actual price
                    is_validated = datetime.utcnow() >= validation_time
                    
                    if actual_price and result.predicted_price:
                        predicted = float(result.predicted_price)
                        error_percentage = abs((predicted - actual_price) / actual_price) * 100
                        accuracy = max(0, 100 - error_percentage)
                
                timeline_data[tf].append({
                    'timestamp': result.timestamp.isoformat() if result.timestamp else None,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'predicted_price': float(result.predicted_price) if result.predicted_price else None,
                    'confidence_score': result.confidence_score,
                    'trend_direction': result.trend_direction,
                    'validation_time': validation_time.isoformat() if result.timestamp else None,
                    'actual_price': actual_price,
                    'actual_price_time': actual_price_time,
                    'accuracy': round(accuracy, 2) if accuracy is not None else None,
                    'error_percentage': round(error_percentage, 2) if error_percentage is not None else None,
                    'is_validated': is_validated if result.timestamp else False
                })
            
            # Get latest analysis time for each timeframe
            latest_analysis = {}
            for tf in timeline_data.keys():
                if timeline_data[tf]:
                    latest_analysis[tf] = timeline_data[tf][0]['timestamp']
            
            # Get database sync time (current time)
            sync_time = datetime.utcnow().isoformat()
            
            db.close()
            
            return jsonify({
                'timeline': timeline_data,
                'latest_analysis': latest_analysis,
                'sync_time': sync_time,
                'count': sum(len(v) for v in timeline_data.values())
            }), 200
        except Exception as e:
            logger.error(f"Error fetching analysis timeline: {e}")
            return jsonify({
                'error': str(e)
            }), 500

