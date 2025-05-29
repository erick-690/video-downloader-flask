from flask import Flask, request, send_file, jsonify
from flask_cors import CORS # Certifique-se de ter instalado: pip install Flask-Cors
import yt_dlp
import os
import uuid

app = Flask(__name__, static_folder='docs')
CORS(app) # Habilita CORS para todas as rotas (necessário se frontend e backend em portas diferentes)

DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/download-video', methods=['POST'])
def download_video():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'URL do vídeo não fornecida'}), 400

    try:
        unique_filename = str(uuid.uuid4())
        # O outtmpl é onde o yt-dlp vai salvar o arquivo localmente.
        # '%(title)s.%(ext)s' é uma boa opção para nomear com o título do vídeo.
        # Mas para o nosso caso, vamos garantir um nome temporário único para o download
        # e depois usar o nome real para o download do navegador.
        temp_output_path_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_filename}.%(ext)s')

        ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # Tenta a melhor qualidade de vídeo e áudio separadas E as mescla, ou usa o melhor formato combinado.
        'outtmpl': temp_output_path_template,
        'noplaylist': True,
        'merge_output_format': 'mp4', # Garante que o FFmpeg mescle para MP4
        'retries': 5,
        'postprocessors': [{ # Garante que o FFmpeg está sendo usado para merge
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
        }],
        'verbose': True, # Mantenha o verbose para ver os logs do yt-dlp
    }

        file_path = None # Inicializa para garantir que está definido
        download_filename = "video_baixado.mp4" # Nome padrão, caso o título não seja extraído

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info) # Obtém o caminho completo do arquivo salvo
            
            # Tenta obter o título e extensão para um nome de download melhor
            if 'title' in info and 'ext' in info:
                # Remove caracteres inválidos para nomes de arquivo e limita o tamanho
                sanitized_title = "".join(c for c in info['title'] if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                download_filename = f"{sanitized_title}.{info['ext']}"
                # Garante que o nome do arquivo não seja muito longo
                if len(download_filename) > 150:
                    download_filename = download_filename[:145] + '.' + info['ext']


        if file_path and os.path.exists(file_path):
            # Define o tipo MIME (pode ser mais específico para outros formatos, mas mp4 é comum)
            mimetype = 'video/mp4' 
            
            # Envia o arquivo com um nome de download específico
            return send_file(
                file_path,
                as_attachment=True,
                download_name=download_filename, # Usa o nome gerado
                mimetype=mimetype # Define o tipo MIME
            )
        else:
            return jsonify({'error': 'Arquivo de vídeo não encontrado após o download.'}), 500

    except yt_dlp.DownloadError as e:
        return jsonify({'error': f'Erro ao baixar o vídeo: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Ocorreu um erro inesperado no servidor: {str(e)}'}), 500


    if __name__ == '__main__':
    # Use Gunicorn em produção (se necessário), Werkzeug localmente
    if os.environ.get('FLASK_ENV') == 'production':
        from gunicorn.app.wsgiapp import run
        run()
    else:
        app.run(debug=True)


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_files(path):
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') # Use 0.0.0.0 para ser acessível de outros dispositivos na rede, se necessário

