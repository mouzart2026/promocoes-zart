export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);

        if (url.pathname === '/api/config') {
            const config = {
                url: env.SUPABASE_URL || 'https://innyohbvgtsoihooykxp.supabase.co',
                anonKey: env.SUPABASE_ANON_KEY || '',
                table: 'ofertas_encontradas',
                select: 'produto_id,titulo,preco_anterior,preco_novo,queda_pct,link,criado_em,plataforma,imagem',
                order: 'criado_em.desc',
                limit: 200
            };
            return new Response(JSON.stringify(config), {
                status: 200,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            });
        }

        return new Response('Not Found', { status: 404 });
    }
};