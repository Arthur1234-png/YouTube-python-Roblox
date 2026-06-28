from flask import Flask, jsonify
from pytubefix import YouTube
import cv2
import os

app = Flask(__name__)

# =====================================================================
# 🔴 LINK DA LIVE DO YOUTUBE (Troque aqui pelo link da transmissão ao vivo)
# =====================================================================
LIVE_URL = "https://www.youtube.com/watch?v=6L3aOGmPHic&pp=0gcJCUELAYcqIYzv" 
# =====================================================================

FRAME_WIDTH, FRAME_HEIGHT = 64, 64
video_captura = None
titulo_atual = "Nenhuma Live ativa"

def conectar_live():
    global video_captura, titulo_atual
    print(f"📡 Conectando à transmissão ao vivo: {LIVE_URL}")
    
    try:
        yt = YouTube(LIVE_URL)
        titulo_atual = yt.title
        print(f"📺 Título da Live: {titulo_atual}")
        
        # Obtém a URL direta do fluxo de transmissão (HLS/m3u8) da live
        stream_url = yt.streaming_data.get("hlsManifestUrl")
        
        if not stream_url:
            # Caso não ache o hlsManifestUrl, tenta buscar o formato padrão de maior compatibilidade
            stream = yt.streams.filter(live_stream=True, file_extension='mp4').first()
            if stream:
                stream_url = stream.url

        if stream_url:
            if video_captura:
                video_captura.release()
            
            # O OpenCV abre o link da transmissão ao vivo como se fosse uma câmera IP
            video_captura = cv2.VideoCapture(stream_url)
            print("✅ Conexão com o fluxo da Live estabelecida com sucesso!")
        else:
            print("❌ Não foi possível extrair o link de transmissão desta Live.")
            
    except Exception as e:
        print(f"❌ Erro ao conectar na Live: {e}")

# Inicia a conexão assim que o script roda
conectar_live()

@app.route("/proximo-frame")
def get_frame():
    global video_captura

    if not video_captura or not video_captura.isOpened():
        return jsonify({"erro": "Transmissão offline ou não conectada no Python."}), 500

    # Captura o frame atual em tempo real da live
    sucesso, frame = video_captura.read()
    
    # Se a live cair ou falhar o frame, tenta reconectar uma vez
    if not sucesso:
        print("⚠️ Fluxo interrompido. Tentando reconectar à Live...")
        conectar_live()
        sucesso, frame = video_captura.read()
        if not sucesso:
            return jsonify({"erro": "A transmissão ao vivo parece ter terminado."}), 500

    try:
        # Redimensiona diretamente no OpenCV (muito mais rápido que converter para PIL)
        frame_redimensionado = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        
        # O OpenCV lê em BGR, convertemos para o padrão RGB do Roblox
        frame_rgb = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGR2RGB)

        # Monta a matriz estruturada [y][x][RGB]
        pixels = []
        for y in range(FRAME_HEIGHT):
            linha = []
            for x in range(FRAME_WIDTH):
                r, g, b = frame_rgb[y, x]
                linha.append([int(r), int(g), int(b)])
            pixels.append(linha)
        
        return jsonify({"pixels": pixels, "status": "ao_vivo"})
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
    
