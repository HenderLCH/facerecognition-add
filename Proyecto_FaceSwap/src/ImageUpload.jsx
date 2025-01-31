import { useState } from "react";
import axios from "axios";

export default function App() {
  const [image, setImage] = useState(null);
  const [targetImage, setTargetImage] = useState(null);
  const [faces, setFaces] = useState([]);
  const [selectedFace, setSelectedFace] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);

  const handleImageChange = (e, type) => {
    const file = e.target.files[0];
    if (file) {
      if (type === "source") setImage(file);
      else setTargetImage(file);
    }
  };

  const detectFaces = async () => {
    if (!image) return alert("Sube una imagen primero");
    
    const formData = new FormData();
    formData.append("image", image);
    
    try {
      const res = await axios.post("http://127.0.0.1:5000/detect-faces", formData);
      setFaces(res.data);
    } catch (error) {
      console.error("Error detectando rostros", error);
    }
  };

  const swapFaces = async () => {
    if (!image || !targetImage) return alert("Sube ambas imágenes primero");
    if (selectedFace === null) return alert("Selecciona una cara");

    const formData = new FormData();
    formData.append("image", image);
    formData.append("target_image", targetImage);
    formData.append("selected_face_id", selectedFace);

    try {
      const res = await axios.post("http://127.0.0.1:5000/swap-face", formData, { responseType: "blob" });
      setPreviewImage(URL.createObjectURL(res.data));
    } catch (error) {
      console.error("Error en el face swap", error);
    }
  };

  const addAccessory = async () => {
    if (!image) return alert("Sube una imagen primero");

    const formData = new FormData();
    formData.append("image", image);

    try {
      const res = await axios.post("http://127.0.0.1:5000/add-accessory", formData, { responseType: "blob" });
      setPreviewImage(URL.createObjectURL(res.data));
    } catch (error) {
      console.error("Error añadiendo accesorio", error);
    }
  };

  const resetApp = () => {
    setImage(null);
    setTargetImage(null);
    setFaces([]);
    setSelectedFace(null);
    setPreviewImage(null);
    document.getElementById("sourceInput").value = "";
    document.getElementById("targetInput").value = "";
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-8">
      <h1 className="text-3xl font-bold mb-4">Alpha Version Horns</h1>

      {/* Cargar imágenes */}
      <div className="flex gap-4">
        <div>
          <input id="sourceInput" type="file" onChange={(e) => handleImageChange(e, "source")} />
          <p className="text-sm text-gray-500">Imagen de origen</p>
        </div>
        {/* <div>
          <input id="targetInput" type="file" onChange={(e) => handleImageChange(e, "target")} />
          <p className="text-sm text-gray-500">Imagen de destino</p>
        </div> */}
      </div>

      {/* Botones de acción */}
      <div className="flex gap-4 mt-4">
        <button className="bg-blue-500 text-white px-4 py-2 rounded" onClick={detectFaces}>
          Detectar Caras
        </button>
        {/* <button className="bg-green-500 text-white px-4 py-2 rounded" onClick={swapFaces} disabled={faces.length === 0}>
          Intercambiar Caras
        </button> */}
        <button className="bg-purple-500 text-white px-4 py-2 rounded" onClick={addAccessory}>
          Agregar Accesorios
        </button>
        <button className="bg-red-500 text-white px-4 py-2 rounded" onClick={resetApp}>
          Reset
        </button>
      </div>

      {/* Mostrar caras detectadas */}
      {faces.length > 0 && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Selecciona una cara:</h2>
          <div className="flex gap-2">
            {faces.map((face) => (
              <img
                key={face.id}
                src={`data:image/png;base64,${face.preview}`}
                alt="Cara detectada"
                className={`w-16 h-16 border-2 ${selectedFace === face.id ? "border-blue-500" : "border-gray-300"} cursor-pointer`}
                onClick={() => setSelectedFace(face.id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Mostrar resultado */}
      {previewImage && (
        <div className="mt-6">
          <h2 className="text-xl font-semibold mb-2">Resultado:</h2>
          <img src={previewImage} alt="Resultado" className="w-64 h-auto border border-gray-300" />
        </div>
      )}
    </div>
  );
}
