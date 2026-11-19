import { test, expect } from '@playwright/test';

/**
 * Phase 1 — Core Chat Assistant
 * Testes de interface web (frontend).
 *
 * Cobre: CT-01 a CT-08 do plano specs/PHASE_1_CORE_CHAT_ASSISTANT.md
 */

const BASE_URL = 'http://127.0.0.1:8001';

test.describe('Interface de Chat — Phase 1', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
  });

  // CT-01 — Carregar a aplicação
  test('CT-01: carrega a aplicação com todos os elementos essenciais', async ({ page }) => {
    await expect(page).toHaveTitle('J.A.R.V.I.S. | Conversas');

    const sidebar = page.locator('aside.sidebar');
    await expect(sidebar).toBeVisible();
    await expect(sidebar).toHaveAttribute('aria-label', 'Conversas');

    await expect(page.getByRole('textbox', { name: 'Sua mensagem' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Enviar mensagem' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Como posso ajudar?' })).toBeVisible();
  });

  // CT-02 — Criar nova conversa
  test('CT-02: cria uma nova conversa ao clicar em "+ Nova conversa"', async ({ page }) => {
    await page.getByRole('button', { name: '+ Nova conversa' }).click();

    await expect(page.locator('#conversation-title')).toHaveText('Nova conversa');
      // Aguarda o status mudar para "Conversa aberta" (operação assíncrona no frontend)
      await expect(page.locator('#status')).toHaveText('Conversa aberta', { timeout: 10000 });
    await expect(page.getByRole('heading', { name: 'Como posso ajudar?' })).toBeVisible();
  });

  // CT-03 — Enviar mensagem e receber resposta (Happy Path)
  test('CT-03: envia mensagem e recebe resposta do Jarvis', async ({ page }) => {
    const message = 'Olá, Jarvis! Tudo bem?';

    await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(message);
    await page.getByRole('button', { name: 'Enviar mensagem' }).click();

    // Aguarda o status indicar resposta recebida (auto-wait do expect)
    await expect(page.locator('#status')).toContainText('Resposta recebida', { timeout: 30000 });

    // Mensagem do usuário aparece
    const userMessages = page.locator('article.message[data-role="user"]');
    await expect(userMessages).toHaveCount(1);
    await expect(userMessages.first()).toContainText(message);

    // Resposta do assistente aparece
    const assistantMessages = page.locator('article.message[data-role="assistant"]');
    await expect(assistantMessages).toHaveCount(1);
    await expect(assistantMessages.first()).toBeVisible();

    // Título da conversa muda para a primeira mensagem
    await expect(page.locator('#conversation-title')).toHaveText(message);
  });

  // CT-04 — Múltiplas mensagens mantêm contexto
  test('CT-04: mantém múltiplas mensagens no histórico da conversa', async ({ page }) => {
    const firstMessage = 'Olá, Jarvis!';
    const secondMessage = 'Qual é o sentido da vida?';

    // Primeira mensagem
    await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(firstMessage);
    await page.getByRole('button', { name: 'Enviar mensagem' }).click();
    await expect(page.locator('#status')).toContainText('Resposta recebida', { timeout: 30000 });

    // Segunda mensagem
    await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(secondMessage);
    await page.getByRole('button', { name: 'Enviar mensagem' }).click();
    await expect(page.locator('#status')).toContainText('Resposta recebida', { timeout: 30000 });

    // Ambas as mensagens do usuário devem estar presentes
    const userMessages = page.locator('article.message[data-role="user"]');
    await expect(userMessages).toHaveCount(2);
    await expect(userMessages.nth(0)).toContainText(firstMessage);
    await expect(userMessages.nth(1)).toContainText(secondMessage);

    // Duas respostas do assistente
    const assistantMessages = page.locator('article.message[data-role="assistant"]');
    await expect(assistantMessages).toHaveCount(2);
  });

  // CT-05 — Navegar pelo histórico
  test('CT-05: navega pelo histórico e carrega conversa anterior', async ({ page }) => {
    // Título único para evitar ambiguidade com sessões de execuções anteriores
    const message = `Conversa histórico ${Date.now()}`;

    // Cria uma conversa com mensagem
    await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(message);
    await page.getByRole('button', { name: 'Enviar mensagem' }).click();
    await expect(page.locator('#status')).toContainText('Resposta recebida', { timeout: 30000 });

      // Cria uma nova conversa (nova sessão) - aguarda status estabilizar
    await page.getByRole('button', { name: '+ Nova conversa' }).click();
      // Aguarda o status mudar para "Conversa aberta" (operação assíncrona no frontend)
      await expect(page.locator('#status')).toHaveText('Conversa aberta', { timeout: 10000 });

    // Clica na conversa anterior no histórico (seletor único por título)
    await page.locator('#conversation-list').getByRole('button', { name: message }).click();

    // O histórico da conversa deve ser carregado
    await expect(page.locator('#conversation-title')).toHaveText(message);
    await expect(page.locator('article.message[data-role="user"]')).toHaveCount(1);
    await expect(page.locator('article.message[data-role="assistant"]')).toHaveCount(1);
  });

  // CT-06 — Validação de campo vazio (UI)
  test('CT-06: não envia mensagem vazia', async ({ page }) => {
    // Tenta enviar com campo vazio
    await page.getByRole('button', { name: 'Enviar mensagem' }).click();

    // Nenhuma mensagem deve ser adicionada
    await expect(page.locator('article.message')).toHaveCount(0);

    // O campo deve permanecer utilizável
    await expect(page.getByRole('textbox', { name: 'Sua mensagem' })).toBeEnabled();
  });

  // CT-07 — Responsividade mobile (375px)
  test('CT-07: layout responsivo sem rolagem horizontal em 375px', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL);

    // Sem rolagem horizontal
    const hasHorizontalScroll = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    expect(hasHorizontalScroll).toBe(false);

    // Elementos essenciais permanecem acessíveis
    await expect(page.getByRole('textbox', { name: 'Sua mensagem' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Enviar mensagem' })).toBeVisible();
    await expect(page.locator('aside.sidebar')).toBeVisible();
  });

  // CT-08 — Acessibilidade
  test('CT-08: elementos possuem atributos de acessibilidade', async ({ page }) => {
    // Sidebar com aria-label
    await expect(page.locator('aside.sidebar')).toHaveAttribute('aria-label', 'Conversas');

    // Região de status
    await expect(page.locator('#status')).toHaveAttribute('role', 'status');

    // Região de anúncio acessível para novas respostas
    await expect(page.locator('#assistant-announcement')).toHaveAttribute('aria-live', 'polite');

    // Link da marca com aria-label
    await expect(page.locator('a.brand')).toHaveAttribute('aria-label', 'J.A.R.V.I.S. início');

    // Campo de mensagem com label associado
    const textbox = page.getByRole('textbox', { name: 'Sua mensagem' });
    await expect(textbox).toBeVisible();
  });
});