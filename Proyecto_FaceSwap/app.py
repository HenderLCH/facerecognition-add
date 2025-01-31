from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
from flask_cors import CORS
from io import BytesIO
from PIL import Image
from insightface.app import FaceAnalysis
from insightface.model_zoo import get_model
import os
import base64

app = Flask(__name__)
CORS(app)

if not os.path.exists("Static"):
    os.makedirs("Static")

# Cargar imagen de cuernos con manejo de errores
try:
    cuernos_img = Image.open(os.path.join("Static", "horns1.png")).convert("RGBA")
except Exception as e:
    print(f"Error cargando cuernos: {str(e)}")
    cuernos_img = None

os.environ["INSIGHTFACE_HOME"] = "D:/InsightFace"
os.environ["INSIGHTFACE_MODELS"] = "D:/InsightFace/models"

face_app = FaceAnalysis(name='buffalo_l_2d106', root="D:/InsightFace/models", providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

def add_horns_to_faces(image):
    """Añade cuernos a cada rostro detectado en la imagen."""
    if cuernos_img is None:
        print("No se encontró la imagen de cuernos")
        return image
    
    img_pil = Image.fromarray(image)
    faces = face_app.get(image)

    for face in faces:
        try:
            bbox = face['bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]

            face_width = x2 - x1
            face_height = y2 - y1

            # Ajustar tamaño de los cuernos
            horns_width = int(face_width * 1)  # Ancho con respecto a la cara
            horns_height = int(horns_width * cuernos_img.height / cuernos_img.width)

            # Posición: centrado horizontalmente, arriba de la cabeza
            horns_x = x1 - int((horns_width - face_width) / 2)
            horns_y = y1 - int(face_height * 0.6)  # Más arriba de la cara

            # Redimensionar cuernos
            horns_resized = cuernos_img.resize((horns_width, horns_height))

            # Pegar sobre la imagen
            img_pil.paste(horns_resized, (horns_x, horns_y), horns_resized)

        except Exception as e:
            print(f"Error colocando cuernos: {str(e)}")
    
    return np.array(img_pil)

@app.route('/add-accessory', methods=['POST'])
def add_accessory():
    """Endpoint para añadir accesorios a la imagen."""
    if 'image' not in request.files:
        return jsonify({"error": "Se requiere una imagen"}), 400
    
    img = np.array(Image.open(request.files['image'].stream).convert("RGB"))
    img_with_horns = add_horns_to_faces(img)

    buffer = BytesIO()
    Image.fromarray(img_with_horns).save(buffer, "PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")

@app.route('/swap-face', methods=['POST'])
def swap_face():
    """Realiza el face swap y agrega cuernos si están disponibles."""
    if 'image' not in request.files or 'target_image' not in request.files:
        return jsonify({"error": "Se requieren ambas imágenes"}), 400

    source_img = np.array(Image.open(request.files['image'].stream).convert("RGB"))
    target_img = np.array(Image.open(request.files['target_image'].stream).convert("RGB"))

    source_faces = face_app.get(source_img)
    target_faces = face_app.get(target_img)

    selected_face_id = int(request.form.get('selected_face_id', 0))
    if selected_face_id >= len(source_faces):
        return jsonify({"error": "ID de cara origen inválido"}), 400

    swapper = get_model('inswapper_128.onnx')
    target_face_id = int(request.form.get('target_face_id', 0))

    if target_face_id < len(target_faces):
        target_img = swapper.get(target_img, target_faces[target_face_id], source_faces[selected_face_id], paste_back=True)

    # Agregar cuernos después del face swap
    target_img_with_horns = add_horns_to_faces(target_img)

    buffer = BytesIO()
    Image.fromarray(target_img_with_horns).save(buffer, "PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png")

@app.route('/detect-faces', methods=['POST'])
def detect_faces():
    file = request.files['image']
    img = Image.open(file.stream).convert("RGB")
    img = np.array(img)

    # Detectar rostros
    faces = face_app.get(img)
    face_data = []
    
    # Extraer la posición y vista previa de cada rostro
    for i, face in enumerate(faces):
        bbox = face['bbox']
        bbox = [int(b) for b in bbox]
        face_img = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
        
        # Codificar la imagen en base64 para que sea compatible con JSON
        _, buffer = cv2.imencode('.png', face_img)
        face_preview = base64.b64encode(buffer).decode('utf-8')  # Convertir bytes a base64 string

        face_data.append({
            "id": i,
            "bbox": bbox,
            "preview": face_preview
        })

    return jsonify(face_data)

# Ruta para detectar caras en la imagen de destino

@app.route('/detect-faces-target', methods=['POST'])
def detect_faces_target():
    if 'target_image' not in request.files:
        return jsonify({"error": "Se requiere una imagen de destino para detectar caras."}), 400

    target_file = request.files['target_image']
    img = Image.open(target_file.stream).convert("RGB")
    img = np.array(img)

    # Detectar rostros
    faces = face_app.get(img)

    if not faces:
        return jsonify({"error": "No se detectaron caras en la imagen de destino."}), 400

    face_data = []
    height, width, _ = img.shape

    def clamp(value, min_value, max_value):
        return max(min_value, min(value, max_value))

    for i, face in enumerate(faces):
        bbox = face['bbox']
        bbox = [int(b) for b in bbox]

        # Asegurar que las coordenadas estén dentro de los límites
        x1 = clamp(bbox[0], 0, width)
        y1 = clamp(bbox[1], 0, height)
        x2 = clamp(bbox[2], 0, width)
        y2 = clamp(bbox[3], 0, height)

        face_img = img[y1:y2, x1:x2]

        # Verificar si face_img no está vacío
        if face_img.size == 0:
            print(f"Advertencia: face_img está vacío para la cara {i}")
            continue  # O maneja el error según corresponda

        # Codificar la imagen en base64 para que sea compatible con JSON
        try:
            _, buffer = cv2.imencode('.png', face_img)
        except cv2.error as e:
            print(f"Error al codificar la cara {i}: {e}")
            continue  # O maneja el error según corresponda

        face_preview = base64.b64encode(buffer).decode('utf-8')  # Convertir bytes a base64 string

        face_data.append({
            "id": i,
            "bbox": [x1, y1, x2, y2],
            "preview": face_preview
        })

    if not face_data:
        return jsonify({"error": "No se pudieron procesar las caras detectadas."}), 400

    return jsonify(face_data)


if __name__ == '__main__':
    app.run(debug=True)
