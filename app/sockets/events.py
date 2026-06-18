from flask_socketio import emit, join_room

def register_events(socketio):

    @socketio.on('connect')
    def on_connect():
        print('Client connected')
        emit('connected', {'message': 'ShieldAI connected'})

    @socketio.on('disconnect')
    def on_disconnect():
        print('Client disconnected')

    @socketio.on('join_dashboard')
    def on_join_dashboard():
        join_room('authority')
        emit('joined', {'room': 'authority'})

    @socketio.on('update_location')
    def on_location_update(data):
        # Broadcast location update to all authority dashboards
        emit('location_update', data, broadcast=True)

    @socketio.on('cancel_alert')
    def on_cancel(data):
        case_id = data.get('case_id')
        emit('case_cancelled', {'case_id': case_id}, broadcast=True)
