class GameSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo aplicamos las cabeceras estrictas en páginas de juego
        if '/jugar/' in request.path:
            response["Cross-Origin-Opener-Policy"] = "same-origin"
            response["Cross-Origin-Embedder-Policy"] = "require-corp"
            response["Cross-Origin-Resource-Policy"] = "cross-origin"
            
            # Importante: Permitir que Tailwind y tus estilos carguen
            response["Access-Control-Allow-Origin"] = "*"
        else:
            # Para el resto de la web mantenemos comportamiento normal
            if not response.has_header("Cross-Origin-Resource-Policy"):
                response["Cross-Origin-Resource-Policy"] = "same-origin"

        return response