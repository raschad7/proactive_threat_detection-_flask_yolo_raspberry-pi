from website import create_app

app = create_app()

if __name__ == '__main__':
    # Run the server on all interfaces so Raspberry Pi can reach it
    app.run(host='0.0.0.0', port=5000, debug=True)
