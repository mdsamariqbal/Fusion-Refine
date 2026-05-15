import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from agents import get_character_description, generate_description, generate_image, evaluate_image, improve_description
from config import MAX_ITERATIONS, TARGET_SCORE

app = Flask(__name__, static_folder='frontend')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend', path)

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    traceback.print_exc()
    return jsonify({"status": "error", "message": f"Global Error: {str(e)}"}), 500

@app.route('/api/fuse', methods=['POST'])
def fuse_characters():
    data = request.json
    char1_name = data.get('char1', 'Pikachu')
    char2_name = data.get('char2', 'Iron Man')

    print(f"Starting fusion for {char1_name} and {char2_name}")

    try:
        char1_desc = get_character_description(char1_name)
        char2_desc = get_character_description(char2_name)

        description = generate_description(char1_desc, char2_desc)
        
        best_score = 0
        best_image = None
        final_prompt = description

        for i in range(1, MAX_ITERATIONS + 1):
            print(f"\n--- Iteration {i} ---")
            
            image_path = generate_image(description, i)
            score, feedback = evaluate_image(image_path, description)
            
            if score > best_score or best_image is None:
                best_score = score
                best_image = image_path
                final_prompt = description
                
            if score >= TARGET_SCORE:
                print("\nTarget achieved!")
                break
                
            print("\nImproving prompt based on feedback...")
            description = improve_description(description, feedback)

        return jsonify({
            "status": "success",
            "image_path": best_image,
            "score": best_score,
            "prompt": final_prompt,
            "char1_desc": char1_desc,
            "char2_desc": char2_desc
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Fusion error: {e}")
        return jsonify({
            "status": "error",
            "message": f"PYTHON_BACKEND_ERROR: {str(e)}"
        }), 500

# Add a route to serve images from the outputs folder (where generate_image saves them)
@app.route('/outputs/<path:filename>')
def serve_output_images(filename):
    return send_from_directory('outputs', filename)

import threading
import webbrowser

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5001")

if __name__ == '__main__':
    # Only open browser once, not on every reloader restart
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.5, open_browser).start()
    app.run(debug=True, port=5001)
