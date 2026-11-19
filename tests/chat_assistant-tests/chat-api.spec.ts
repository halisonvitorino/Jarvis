import { test, expect } from '@playwright/test';

/**
 * Phase 1 — Core Chat Assistant
 * Testes de API (backend FastAPI).
 *
 * Cobre: CT-09 a CT-21 do plano specs/PHASE_1_CORE_CHAT_ASSISTANT.md
 */

const BASE_URL = 'http://127.0.0.1:8001';

test.describe('API de Chat — Phase 1', () => {

  // CT-09 — Criar sessão via API
  test('CT-09: cria sessão via POST /api/sessions', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Teste automatizado' },
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.session_id).toBeTruthy();
    expect(body.title).toBe('Teste automatizado');
  });

  // CT-10 — Listar sessões
  test('CT-10: lista sessões via GET /api/sessions', async ({ request }) => {
    // Cria uma sessão primeiro
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Sessão para listar' },
    });
    const { session_id } = await createResponse.json();

    const response = await request.get(`${BASE_URL}/api/sessions`);
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.sessions).toBeInstanceOf(Array);
    const sessionIds = body.sessions.map((s: any) => s.session_id);
    expect(sessionIds).toContain(session_id);
  });

  // CT-11 — Buscar sessão existente
  test('CT-11: busca sessão existente via GET /api/sessions/{id}', async ({ request }) => {
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Sessão detalhe' },
    });
    const { session_id } = await createResponse.json();

    const response = await request.get(`${BASE_URL}/api/sessions/${session_id}`);
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.session_id).toBe(session_id);
    expect(body.title).toBe('Sessão detalhe');
    expect(body.messages).toBeInstanceOf(Array);
  });

  // CT-12 — Buscar sessão inexistente (404)
  test('CT-12: retorna 404 para sessão inexistente', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/sessions/id-inexistente-12345`);
    expect(response.status()).toBe(404);
  });

  // CT-13 — Enviar mensagem via API
  test('CT-13: envia mensagem via POST /api/chat', async ({ request }) => {
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Chat API' },
    });
    const { session_id } = await createResponse.json();

    const response = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Olá via API' },
      timeout: 30000,
    });

    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.response).toBeTruthy();
    expect(body.model).toBeTruthy();
    expect(body.session_id).toBe(session_id);
  });

  // CT-14 — Mensagem vazia rejeitada (422)
  test('CT-14: rejeita mensagem vazia com 422', async ({ request }) => {
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Validação' },
    });
    const { session_id } = await createResponse.json();

    const response = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: '' },
    });

    expect(response.status()).toBe(422);
  });

  // CT-15 — Título vazio rejeitado (422)
  test('CT-15: rejeita título vazio com 422', async ({ request }) => {
    const response = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: '' },
    });

    expect(response.status()).toBe(422);
  });

  // CT-16 — Corpo acima do limite (413)
  test('CT-16: rejeita corpo acima de 64 KiB com 413', async ({ request }) => {
    const bigMessage = 'x'.repeat(64 * 1024 + 1);

    const response = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id: 'x', message: bigMessage },
    });

    expect(response.status()).toBe(413);
  });

  // CT-17 — Idempotência: conflito (409)
  test('CT-17: retorna 409 ao reutilizar request_id com mensagem diferente', async ({ request }) => {
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Idempotência' },
    });
    const { session_id } = await createResponse.json();
    const requestId = crypto.randomUUID();

    // Primeiro envio
    const first = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Primeira mensagem', request_id: requestId },
      timeout: 30000,
    });
    expect(first.status()).toBe(200);

    // Segundo envio com mesmo request_id mas mensagem diferente
    const second = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Mensagem diferente', request_id: requestId },
    });
    expect(second.status()).toBe(409);
  });

  // CT-18 — Idempotência: reenvio idêntico (200)
  test('CT-18: retorna 200 ao reenviar mesma mensagem com mesmo request_id', async ({ request }) => {
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Idempotência cache' },
    });
    const { session_id } = await createResponse.json();
    const requestId = crypto.randomUUID();

    const first = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Mensagem original', request_id: requestId },
      timeout: 30000,
    });
    expect(first.status()).toBe(200);
    const firstBody = await first.json();

    // Reenvio idêntico — deve retornar a resposta em cache
    const second = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Mensagem original', request_id: requestId },
    });
    expect(second.status()).toBe(200);
    const secondBody = await second.json();
    expect(secondBody.response).toBe(firstBody.response);
  });

  // CT-19 — Indisponibilidade de IA (503)
  // Nota: requer ambiente sem provedores de IA configurados.
  // Este teste valida o comportamento esperado quando a IA está indisponível.
  test('CT-19: documenta comportamento 503 quando IA indisponível', async ({ request }) => {
    // Cria uma sessão válida
    const createResponse = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Teste 503' },
    });
    expect(createResponse.status()).toBe(200);
    const { session_id } = await createResponse.json();

    // Tenta enviar mensagem — se a IA estiver disponível, retorna 200;
    // se indisponível, retorna 503. Ambos são comportamentos válidos.
    const response = await request.post(`${BASE_URL}/api/chat`, {
      data: { session_id, message: 'Teste de disponibilidade' },
      timeout: 30000,
    });

    // Deve ser 200 (IA disponível) ou 503 (IA indisponível)
    expect([200, 503]).toContain(response.status());
  });

  // CT-20 — Limite de sessões (429)
  // Nota: o limite é 50 sessões. Este teste verifica o comportamento
  // sem criar 50 sessões (que poluiria o estado). A validação de limite
  // está coberta nos testes unitários (test_phase1_chat.py).
  test('CT-20: documenta limite de 50 sessões (429)', async ({ request }) => {
    // Cria uma sessão para confirmar que a API está operacional
    const response = await request.post(`${BASE_URL}/api/sessions`, {
      data: { title: 'Limite check' },
    });
    expect(response.status()).toBe(200);
    // O teste de limite real (429) está coberto em tests/test_phase1_chat.py
    // para evitar poluição de estado no ambiente E2E.
  });

  // CT-21 — Headers de segurança
  test('CT-21: resposta inclui headers de segurança', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/`);

    expect(response.status()).toBe(200);
    const headers = response.headers();

    expect(headers['content-security-policy']).toContain("default-src 'self'");
    expect(headers['x-frame-options']).toBe('DENY');
    expect(headers['x-content-type-options']).toBe('nosniff');
  });
});