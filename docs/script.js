document.addEventListener('DOMContentLoaded', () => {
    const videoLinkInput = document.getElementById('videoLink');
    const downloadButton = document.getElementById('downloadButton');
    const messageDiv = document.getElementById('message');
    const loadingDiv = document.getElementById('loading');

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
            // A requisição POST para o backend
            const response = await fetch('/download-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: videoLink })
            });

            if (response.ok) {
                // Se o backend retornou um arquivo, o navegador vai lidar com o download automaticamente.
                // Não é necessário ler a resposta aqui se o objetivo é um download de arquivo.
                messageDiv.textContent = 'Download iniciado!';
                messageDiv.classList.add('success');
            } else {
                // Se o backend retornou um erro (ex: 400, 500)
                const errorData = await response.json(); // Tenta ler a resposta JSON de erro do backend
                messageDiv.textContent = `Erro: ${errorData.error || 'Ocorreu um erro ao processar o vídeo.'}`;
                messageDiv.classList.add('error'); // Você pode adicionar uma classe 'error' no CSS
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