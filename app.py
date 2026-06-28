from flask import Flask, jsonify, request
from pytubefix import YouTube
from moviepy import VideoFileClip
from PIL import Image
import os

app = Flask(__name__)

# CONFIGURAÇÕES
video_path = "video.mp4"
frame_width, frame_height = 64, 64
fps = 10
frame_index = 0
clip = None
total_frames = 0
titulo_atual = "Nenhum vídeo carregado"

# 1. ROTA PARA BAIXAR E CARREGAR O VÍDEO DINAMICAMENTE
@app.route('/carregar-video', methods=['POST'])
def carregar_video():
    global clip, total_frames, frame_index, titulo_atual
    dados = request.json or {}
    url = dados.get("url")
    
    if not url:
        return jsonify({"status": "erro", "mensagem": "A URL fornecida está vazia"}), 400
        
    try:
        print(f"Baixando a URL do YouTube: {url}")
        yt = YouTube(url)
        titulo_atual = yt.title
        
        # Fecha o clip anterior para liberar o arquivo se ele existir
        if clip:
            clip.close()
            
        if os.path.exists(video_path):
            os.remove(video_path)
            
        # Baixa em 360p para não estourar a RAM do plano gratuito da Render
        stream = yt.streams.filter(progressive=True, file_extension='mp4', res="360p").first()
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').asc().first()
            
        stream.download(filename=video_path)
        print("✅ Vídeo baixado com sucesso!")
        
        # Carrega o novo vídeo na memória via MoviePy
        clip = VideoFileClip(video_path)
        total_frames = int(clip.duration * fps)
        frame_index = 0 # Reinicia o contador de frames
        
        return jsonify({"status": "sucesso", "mensagem": f"Tocando: {titulo_atual}"})
        
    except Exception as e:
        print(f"Erro ao processar: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# 2. SERVIR FRAMES EM LOOP (Formato de matriz tridimensional [y][x][RGB])
@app.route("/proximo-frame")
def get_frame():
    global frame_index, clip, total_frames
    
    if not clip:
        return jsonify({"erro": "Nenhum vídeo ativo. Cole um link primeiro."}), 400

    # Calcula tempo do frame atual
    t = (frame_index % total_frames) / fps
    frame_index += 1

    # Extrai frame e redimensiona
    frame = clip.get_frame(t)
    img = Image.fromarray(frame).resize((frame_width, frame_height)).convert("RGB")

    # Converte pixels pra estrutura JSON [y][x][RGB] idêntica à sua
    pixels = [
        [[int(r), int(g), int(b)] for r, g, b in [img.getpixel((x, y)) for x in range(frame_width)]]
        for y in range(frame_height)
    ]

    return jsonify({"pixels": pixels})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    