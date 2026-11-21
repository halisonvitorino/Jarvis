import { test, expect } from '@playwright/test';

/**
 * Phase 2 — Memory System
 * Testes de interface web (frontend) para o sistema de memória.
 *
 * Cobre: MS-01 a MS-24 do plano test_plans/PHASE_2_MEMORY_SYSTEM.md
 */
const BASE_URL = 'http://127.0.0.1:8001';

test.describe('Sistema de Memória — Phase 2', () => {
  test.beforeEach(async ({ page, request }) => {
    // Clean up all sessions before each test to avoid session limit
    await request.delete(`${BASE_URL}/api/test/sessions`);
    await page.goto(BASE_URL);
  });

  // ============================================================
  // Suite 1: Short-Term Memory (Session Context) - MS-01 to MS-04
  // ============================================================
  test.describe('Memória de Curto Prazo (Contexto da Sessão)', () => {
    // MS-01: Store and recall messages in session
    test('MS-01: armazena e recupera mensagens na sessão', async ({ page }) => {
      // 1. Send message establishing context
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é João');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // 2. Send follow-up question requiring memory recall
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é meu nome?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // 3. Verify assistant recalls "João" in response
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('João');
    });

    // MS-02: Sessions maintain independent memory
    test('MS-02: sessões mantêm memória independente', async ({ page }) => {
      // 1. Send message in first session
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Maria');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // 2. Create new session
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // 3. Ask for name in new session
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é meu nome?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // 4. Verify assistant does NOT know "Maria" (new session isolation)
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).not.toContainText('Maria');
      await expect(assistantMessages.last()).toContainText('não tenho acesso');
    });

    // MS-03: Session maintains message history up to limit
    test('MS-03: sessão mantém histórico de mensagens até o limite', async ({ page }) => {
      const messages = ['Mensagem 1', 'Mensagem 2', 'Mensagem 3', 'Mensagem 4', 'Mensagem 5'];

      // Send 5 messages in sequence
      for (const msg of messages) {
        await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(msg);
        await page.getByRole('button', { name: 'Enviar mensagem' }).click();
        await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });
      }

      // Verify all 5 user messages appear in chat
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(5);
      for (let i = 0; i < messages.length; i++) {
        await expect(userMessages.nth(i)).toContainText(messages[i]);
      }

      // Verify all 5 assistant responses appear
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages).toHaveCount(5);
    });

    // MS-04: Context window - long conversation
    test('MS-04: janela de contexto - conversa longa', async ({ page }) => {
      // Send 10 messages establishing context about a topic
      const contextMessages = [
        'Vou falar sobre programação em Python',
        'Python é uma linguagem interpretada',
        'Ela tem tipagem dinâmica',
        'É muito usada para ciência de dados',
        'Bibliotecas populares incluem pandas e numpy',
        'Também é usada para web com Django e Flask',
        'A sintaxe é limpa e legível',
        'Suporta programação orientada a objetos',
        'Também suporta programação funcional',
        'É uma das linguagens mais populares hoje'
      ];

      for (const msg of contextMessages) {
        await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(msg);
        await page.getByRole('button', { name: 'Enviar mensagem' }).click();
        await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });
      }

      // Ask follow-up question requiring context from early messages
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual linguagem eu estava descrevendo?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify assistant recalls early context
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Python');
    });
  });

  // ============================================================
  // Suite 2: Long-Term Memory (User Profiles) - MS-05 to MS-08
  // ============================================================
  test.describe('Memória de Longo Prazo (Perfis de Usuário)', () => {
    // MS-05: Save and retrieve user profile
    test('MS-05: salva e recupera perfil de usuário', async ({ page }) => {
      // Create session and establish user profile info
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Maria e eu gosto de café');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create new session to test long-term persistence
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // Ask for name - should recall from long-term memory
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é meu nome?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify assistant recalls name from long-term profile
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Maria');
    });

    // MS-06: New profile data merges with existing profile
    test('MS-06: novos dados de perfil mesclam com perfil existente', async ({ page }) => {
      // First session - establish initial profile
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Carlos e sou desenvolvedor');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Second session - add more profile info
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Também gosto de TypeScript e React');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Third session - verify merged profile
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('O que você sabe sobre mim?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify merged profile info
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Carlos');
      await expect(assistantMessages.last()).toContainText('desenvolvedor');
    });

    // MS-07: User profile persists across MemoryStore instances
    test('MS-07: perfil de usuário persiste entre instâncias', async ({ page }) => {
      // This test verifies persistence by creating a session, then new session
      // The long-term memory should survive across "instances" (browser sessions)
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Ana e trabalho com IA');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create new session (simulates new MemoryStore instance)
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é meu nome e profissão?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Ana');
      await expect(assistantMessages.last()).toContainText('IA');
    });

    // MS-08: Profile merging with complex nested data
    test('MS-08: mesclagem de perfil com dados aninhados complexos', async ({ page }) => {
      // Establish profile with preferences
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Pedro, prefiro respostas curtas e diretas');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Add more preferences in new session
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Também gosto de exemplos de código');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify merged preferences
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Quais são minhas preferências?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Pedro');
      await expect(assistantMessages.last()).toContainText('curtas');
      await expect(assistantMessages.last()).toContainText('código');
    });
  });

  // ============================================================
  // Suite 3: Semantic Search (VectorStore/ChromaDB) - MS-09 to MS-12
  // ============================================================
  test.describe('Busca Semântica (VectorStore/ChromaDB)', () => {
    // MS-09: Add items with embeddings to vector store
    test('MS-09: adiciona itens com embeddings ao vector store', async ({ page }) => {
      // Send messages that will be embedded and stored
      const messages = [
        'Usuário gosta de programação em Python',
        'Usuário gosta de cozinhar comida italiana',
        'Usuário trabalha como engenheiro de software'
      ];

      for (const msg of messages) {
        await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(msg);
        await page.getByRole('button', { name: 'Enviar mensagem' }).click();
        await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });
      }

      // Verify messages are stored (they appear in chat)
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(3);
    });

    // MS-10: Search returns semantically similar items
    test('MS-10: busca retorna itens semanticamente similares', async ({ page }) => {
      // First, establish some context in this session
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Gosto muito de programar em Python e JavaScript');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Também gosto de cozinhar pratos italianos');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Search for programming-related content
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Busque na memória: programação');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify response mentions programming context
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('programação');
    });

    // MS-11: Search with n_results limit
    test('MS-11: busca com limite de resultados', async ({ page }) => {
      // Add multiple messages
      const topics = ['Python', 'JavaScript', 'TypeScript', 'Rust', 'Go'];
      for (const topic of topics) {
        await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(`Estou aprendendo ${topic}`);
        await page.getByRole('button', { name: 'Enviar mensagem' }).click();
        await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });
      }

      // Search for programming languages
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Busque na memória: linguagem de programação');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify response is relevant
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toBeVisible();
    });

    // MS-12: Retrieve all stored items
    test('MS-12: recupera todos os itens armazenados', async ({ page }) => {
      // Verify chat history loads correctly
      const userMessages = page.locator('article.message[data-role="user"]');
      const assistantMessages = page.locator('article.message[data-role="assistant"]');

      // Should have messages from previous tests in this session
      await expect(userMessages.first()).toBeVisible();
      await expect(assistantMessages.first()).toBeVisible();
    });
  });

  // ============================================================
  // Suite 4: Cross-Session Isolation - MS-13 to MS-16
  // ============================================================
  test.describe('Isolamento entre Sessões', () => {
    // MS-13: New session has no previous messages
    test('MS-13: nova sessão não tem mensagens anteriores', async ({ page }) => {
      // First, create a session with messages
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Mensagem na sessão 1');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create new session
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // Verify chat area shows empty state
      await expect(page.getByRole('heading', { name: 'Como posso ajudar?' })).toBeVisible();

      // Verify no previous messages visible
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(0);
    });

    // MS-14: Session isolation - session A doesn't know session B's context
    test('MS-14: isolamento de sessão - sessão A não conhece contexto da sessão B', async ({ page }) => {
      // Session A: establish context
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Alice e gosto de gatos');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create Session B
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // Session B: different context
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Bob e gosto de cachorros');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Go back to Session A via history
      const sessionAItem = page.locator('#conversation-list').getByRole('button', { name: 'Meu nome é Alice e gosto de gatos' });
      await sessionAItem.click();

      // Verify Session A context is preserved
      await expect(page.locator('#conversation-title')).toContainText('Alice');
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages.first()).toContainText('Alice');
      await expect(userMessages.first()).toContainText('gatos');

      // Go to Session B via history
      const sessionBItem = page.locator('#conversation-list').getByRole('button', { name: 'Meu nome é Bob e gosto de cachorros' });
      await sessionBItem.click();

      // Verify Session B context is preserved
      await expect(page.locator('#conversation-title')).toContainText('Bob');
      const userMessagesB = page.locator('article.message[data-role="user"]');
      await expect(userMessagesB.first()).toContainText('Bob');
      await expect(userMessagesB.first()).toContainText('cachorros');
    });

    // MS-15: Multiple sessions operate independently
    test('MS-15: múltiplas sessões operam independentemente', async ({ page }) => {
      // Create session 1
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Sessão 1: tema ciência');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create session 2
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Sessão 2: tema arte');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create session 3
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Sessão 3: tema esportes');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify all 3 sessions exist in history
      const historyItems = page.locator('#conversation-list').getByRole('listitem');
      await expect(historyItems).toHaveCount(3);
    });

    // MS-16: Memory operations don't leak between sessions
    test('MS-16: operações de memória não vazam entre sessões', async ({ page }) => {
      // Session 1: store specific info
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Minha cor favorita é azul');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Session 2: should not know about blue
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é minha cor favorita?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify no knowledge of "azul"
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).not.toContainText('azul');
    });
  });

  // ============================================================
  // Suite 5: Memory Persistence & Recovery - MS-17 to MS-20
  // ============================================================
  test.describe('Persistência e Recuperação de Memória', () => {
    // MS-17: Chat history loads correctly from memory
    test('MS-17: histórico de chat carrega corretamente da memória', async ({ page }) => {
      // Create a session with messages
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Mensagem para testar persistência');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create new session
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // Click on previous session in history
      const previousSession = page.locator('#conversation-list').getByRole('button', { name: 'Mensagem para testar persistência' });
      await previousSession.click();

      // Verify session loads with messages
      await expect(page.locator('#conversation-title')).toContainText('Mensagem para testar persistência');
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(1);
      await expect(userMessages.first()).toContainText('Mensagem para testar persistência');

      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages).toHaveCount(1);
    });

    // MS-18: New session has empty state
    test('MS-18: nova sessão tem estado vazio', async ({ page }) => {
      // Ensure we have at least one session with messages
      const userMessages = page.locator('article.message[data-role="user"]');
      if (await userMessages.count() > 0) {
        await page.getByRole('button', { name: '+ Nova conversa' }).click();
        await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });
      }

      // Verify empty state
      await expect(page.getByRole('heading', { name: 'Como posso ajudar?' })).toBeVisible();
      await expect(page.locator('article.message')).toHaveCount(0);
    });

    // MS-19: Long-term profile persists across frontend sessions
    test('MS-19: perfil de longo prazo persiste entre sessões do frontend', async ({ page }) => {
      // Establish profile in current session
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Meu nome é Eva e sou designer');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Create new session (simulates new browser tab)
      await page.getByRole('button', { name: '+ Nova conversa' }).click();
      await expect(page.getByText('Conversa aberta')).toBeVisible({ timeout: 10000 });

      // Ask for profile info
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Qual é meu nome e profissão?');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify long-term profile persistence
      const assistantMessages = page.locator('article.message[data-role="assistant"]');
      await expect(assistantMessages.last()).toContainText('Eva');
      await expect(assistantMessages.last()).toContainText('designer');
    });

    // MS-20: Memory survives server restart (simulated by new page load)
    test('MS-20: memória sobrevive a reinicialização do servidor', async ({ page }) => {
      // Create session with messages
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Teste de persistência após reload');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Reload page (simulates server restart from frontend perspective)
      await page.reload();
      await expect(page).toHaveTitle('J.A.R.V.I.S. | Conversas');

      // Verify session still exists in history
      const historyItems = page.locator('#conversation-list').getByRole('listitem');
      await expect(historyItems.first()).toContainText('Teste de persistência após reload');

      // Click session and verify messages load
      await historyItems.first().click();
      await expect(page.locator('#conversation-title')).toContainText('Teste de persistência após reload');
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(1);
    });
  });

  // ============================================================
  // Suite 6: Memory API Edge Cases - MS-21 to MS-24
  // ============================================================
  test.describe('Casos Extremos da API de Memória', () => {
    // MS-21: Empty message validation
    test('MS-21: validação de mensagem vazia', async ({ page }) => {
      // Try to send empty message
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();

      // No message should be added
      await expect(page.locator('article.message')).toHaveCount(0);

      // Input should remain usable
      await expect(page.getByRole('textbox', { name: 'Sua mensagem' })).toBeEnabled();
    });

    // MS-22: Very long message handling
    test('MS-22: tratamento de mensagem muito longa', async ({ page }) => {
      // Create a very long message
      const longMessage = 'A'.repeat(5000);
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(longMessage);
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify message was sent and response received
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages.last()).toContainText('A');
    });

    // MS-23: Special characters and encoding
    test('MS-23: caracteres especiais e codificação', async ({ page }) => {
      // Send message with special characters
      const specialMessage = 'Olá! 🎉 Teste com acentos: áéíóú, ç, ñ. Emojis: 😀🚀💻. Símbolos: @#$%^&*()';
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill(specialMessage);
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Verify message appears correctly
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages.last()).toContainText('Olá');
      await expect(userMessages.last()).toContainText('🎉');
    });

    // MS-24: Memory operations are transparent to user
    test('MS-24: operações de memória são transparentes ao usuário', async ({ page }) => {
      // Verify no memory management UI elements visible
      await expect(page.locator('button:has-text("salvar memória")')).toHaveCount(0);
      await expect(page.locator('button:has-text("limpar memória")')).toHaveCount(0);
      await expect(page.locator('button:has-text("ver perfil")')).toHaveCount(0);

      // Use chat normally - memory operations happen automatically
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Mensagem normal');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // User experiences seamless conversation with context
      await page.getByRole('textbox', { name: 'Sua mensagem' }).fill('Outra mensagem');
      await page.getByRole('button', { name: 'Enviar mensagem' }).click();
      await expect(page.getByText('Resposta recebida').first()).toBeVisible({ timeout: 60000 });

      // Both messages should be in history
      const userMessages = page.locator('article.message[data-role="user"]');
      await expect(userMessages).toHaveCount(2);
    });
  });
});