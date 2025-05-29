document.addEventListener('DOMContentLoaded', () => {
    const videoLinkInput = document.getElementById('videoLink');
    const downloadButton = document.getElementById('downloadButton');
    const messageDiv = document.getElementById('message');
    const loadingDiv = document.getElementById('loading');

    // URL do seu backend hospedado no Render.com
    // Lembre-se de substituir pela SUA URL real do Render.com
    const BACKEND_URL = 'https://meu-baixador-de-videos.onrender.com'; // <--- MUDE AQUI!

    downloadButton.addEventListener('click', async () => {
        const videoLink = videoLinkInput.value.trim();
        messageDiv.textContent = '';
        messageDiv.className = 'message';
        loadingDiv.style.display = 'none';

        if (!videoLink) {
            messageDiv.textContent = 'Por favor, insira um link de vídeo.';
            return;
        }

        loadingDiv.style.display = 'block';

        try {
            const response = await fetch(`${BACKEND_URL}/download-video`, { // <--- USE A VARIÁVEL
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: videoLink })
            });

            if (response.ok) {
                messageDiv.textContent = 'Download iniciado!';
                messageDiv.classList.add('success');
                // O navegador lida com o download do arquivo enviado pelo backend
            } else {
                const errorData = await response.json();
                messageDiv.textContent = `Erro: ${errorData.error || 'Ocorreu um erro ao processar o vídeo.'}`;
                messageDiv.classList.add('error');
            }
        } catch (error) {
            console.error('Erro na requisição Fetch:', error);
            messageDiv.textContent = 'Não foi possível conectar ao servidor ou houve um erro de rede.';
            messageDiv.classList.add('error');
        } finally {
            loadingDiv.style.display = 'none';
        }
    });
});