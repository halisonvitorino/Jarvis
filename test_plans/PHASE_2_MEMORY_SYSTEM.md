# Phase 2 Memory System Test Plan

## Application Overview

JARVIS Phase 2 Memory System implements persistent memory for the AI assistant with three layers: (1) Short-term memory per session using JSON storage, (2) Long-term user profiles with merge capabilities, and (3) Semantic search via ChromaDB vector store with 384-dim embeddings. The MemoryManager facade integrates all components and is used by ConversationManager during chat operations. The frontend has no explicit memory UI - memory is transparent to users.

## Test Scenarios

### 1. Short-term Memory (Per Session)

**Seed:** `tests/seed.spec.ts`

#### 1.1. Store and recall messages in session

**File:** `tests/memory-system-tests/short-term-memory.spec.ts`

**Steps:**
  1. Given a fresh MemoryStore instance
    - expect: MemoryStore initializes with empty sessions and profiles
  2. When calling remember() with session_id='session-1', role='user', content='Hello JARVIS'
    - expect: Entry is stored with role and content
    - expect: Entry is persisted to short_term.json
  3. When calling remember() with session_id='session-1', role='assistant', content='Hello! How can I help?'
    - expect: Second entry is appended to same session
    - expect: Session now has 2 messages in chronological order
  4. When calling recall('session-1')
    - expect: Returns list of message contents in order: ['Hello JARVIS', 'Hello! How can I help?']
  5. When calling recall('non-existent-session')
    - expect: Returns empty list

#### 1.2. Sessions maintain independent memory

**File:** `tests/memory-system-tests/session-isolation.spec.ts`

**Steps:**
  1. Given a fresh MemoryStore instance
    - expect: MemoryStore initializes with empty sessions
  2. When storing messages in session-1: 'User prefers short answers'
    - expect: Message stored in session-1
  3. When storing messages in session-2: 'User likes detailed explanations'
    - expect: Message stored in session-2
  4. When recalling session-1
    - expect: Returns only session-1 messages
    - expect: Does not contain session-2 messages
  5. When recalling session-2
    - expect: Returns only session-2 messages
    - expect: Does not contain session-1 messages

#### 1.3. Session maintains message history up to limit

**File:** `tests/memory-system-tests/context-window.spec.ts`

**Steps:**
  1. Given a fresh MemoryStore instance
    - expect: MemoryStore initializes with empty sessions
  2. When adding 25 messages to session-1 (exceeding typical context window)
    - expect: All 25 messages are stored in memory
    - expect: recall() returns all 25 messages in order
  3. When calling get_context_summary('session-1')
    - expect: Returns formatted string with all messages as 'role: content' lines

### 2. Long-term Memory (User Profiles)

**Seed:** `tests/seed.spec.ts`

#### 2.1. Save and retrieve user profile

**File:** `tests/memory-system-tests/long-term-memory.spec.ts`

**Steps:**
  1. Given a fresh MemoryStore instance
    - expect: MemoryStore initializes with empty profiles
  2. When calling save_profile('owner', {'name': 'João', 'preferences': ['short answers', 'direct language']})
    - expect: Profile is stored with name and preferences
    - expect: Profile is persisted to long_term.json
  3. When calling get_profile('owner')
    - expect: Returns profile with name='João'
    - expect: Returns preferences list containing 'short answers' and 'direct language'
  4. When calling get_profile('non-existent')
    - expect: Returns empty dictionary

#### 2.2. New profile data merges with existing profile

**File:** `tests/memory-system-tests/profile-merging.spec.ts`

**Steps:**
  1. Given a MemoryStore with existing profile 'owner' containing name='João', preferences=['short answers']
    - expect: Profile exists with initial data
  2. When calling save_profile('owner', {'preferences': ['short answers', 'direct language'], 'facts': ['Prefers direct responses']})
    - expect: Profile is updated with merged data
  3. When calling get_profile('owner')
    - expect: name remains 'João'
    - expect: preferences contains both 'short answers' and 'direct language' (no duplicates)
    - expect: facts contains 'Prefers direct responses'
  4. When saving profile with dict value that merges with existing dict
    - expect: Dict values are merged (not replaced)
  5. When saving profile with list value that merges with existing list
    - expect: List values are concatenated and deduplicated

#### 2.3. User profile persists across MemoryStore instances

**File:** `tests/memory-system-tests/cross-session-persistence.spec.ts`

**Steps:**
  1. Given first MemoryStore instance saves profile 'owner' with name='João'
    - expect: Profile saved to long_term.json
  2. When creating second MemoryStore instance with same storage_dir
    - expect: Second instance loads existing profile from disk
  3. When calling get_profile('owner') on second instance
    - expect: Returns profile with name='João'

### 3. Semantic Search (VectorStore)

**Seed:** `tests/seed.spec.ts`

#### 3.1. Add items with embeddings to vector store

**File:** `tests/memory-system-tests/vector-store-add.spec.ts`

**Steps:**
  1. Given a fresh VectorStore instance
    - expect: ChromaDB client initialized
    - expect: Collection 'jarvis_memory' created or retrieved
  2. When calling add_items() with ids=['msg-1', 'msg-2'], embeddings=[[0.1]*384, [0.2]*384], metadatas=[{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi there!'}]
    - expect: Items are added to ChromaDB collection
    - expect: No exception is raised
  3. When calling add_items() with mismatched array lengths
    - expect: Exception is raised

#### 3.2. Search returns semantically similar items

**File:** `tests/memory-system-tests/vector-store-search.spec.ts`

**Steps:**
  1. Given VectorStore with items: 'User likes Python programming', 'User enjoys cooking Italian food', 'User works as software engineer'
    - expect: Items are stored with embeddings
  2. When calling search() with query embedding for 'programming'
    - expect: Returns results with 'Python programming' item ranked highest
    - expect: Returns up to n_results items
    - expect: Results include ids, distances, and metadatas
  3. When calling search() with n_results=2
    - expect: Returns at most 2 results
  4. When calling search() on empty collection
    - expect: Returns empty results structure

#### 3.3. Retrieve all stored items

**File:** `tests/memory-system-tests/vector-store-get-all.spec.ts`

**Steps:**
  1. Given VectorStore with multiple items
    - expect: Items exist in collection
  2. When calling get_all_items()
    - expect: Returns all items with ids, embeddings, and metadatas

### 4. MemoryManager Facade

**Seed:** `tests/seed.spec.ts`

#### 4.1. Update session memory

**File:** `tests/memory-system-tests/memory-manager-update.spec.ts`

**Steps:**
  1. Given a fresh MemoryManager instance
    - expect: MemoryManager initializes with MemoryStore
  2. When calling update_session_memory('session-1', 'user', 'My name is Alice')
    - expect: Returns entry with role='user' and content='My name is Alice'
    - expect: Message is stored in session memory
  3. When calling update_session_memory('session-1', 'assistant', 'Nice to meet you, Alice!')
    - expect: Returns entry with role='assistant'
    - expect: Session now has 2 messages

#### 4.2. Retrieve all messages for a session

**File:** `tests/memory-system-tests/memory-manager-recall.spec.ts`

**Steps:**
  1. Given MemoryManager with session 'session-1' containing 3 messages
    - expect: Session has messages stored
  2. When calling recall_session('session-1')
    - expect: Returns list of 3 message contents in chronological order
  3. When calling recall_session('non-existent')
    - expect: Returns empty list

#### 4.3. Manage user profiles through MemoryManager

**File:** `tests/memory-system-tests/memory-manager-profile.spec.ts`

**Steps:**
  1. Given a fresh MemoryManager instance
    - expect: MemoryManager initializes
  2. When calling save_user_profile('owner', {'name': 'Bob', 'role': 'developer'})
    - expect: Returns merged profile with name and role
  3. When calling get_user_profile('owner')
    - expect: Returns profile with name='Bob', role='developer'
  4. When calling get_user_profile('unknown')
    - expect: Returns empty dictionary

#### 4.4. Search session history for query string

**File:** `tests/memory-system-tests/memory-manager-search-history.spec.ts`

**Steps:**
  1. Given MemoryManager with session 'session-1' containing messages: 'I like Python', 'Python is great', 'I prefer JavaScript'
    - expect: Session has messages
  2. When calling search_history('session-1', 'Python')
    - expect: Returns messages containing 'Python' (case-insensitive)
    - expect: Returns 2 messages: 'I like Python', 'Python is great'
  3. When calling search_history('session-1', 'python')
    - expect: Returns same results (case-insensitive)
  4. When calling search_history('session-1', '')
    - expect: Returns empty list
  5. When calling search_history('session-1', '   ')
    - expect: Returns empty list
  6. When calling search_history('non-existent', 'Python')
    - expect: Returns empty list

#### 4.5. Generate full context summary for session

**File:** `tests/memory-system-tests/memory-manager-context.spec.ts`

**Steps:**
  1. Given MemoryManager with session 'session-1' containing: user: 'Hello', assistant: 'Hi there!'
    - expect: Session has messages
  2. When calling get_all_context('session-1')
    - expect: Returns formatted string: 'user: Hello\nassistant: Hi there!'
  3. When calling get_all_context('non-existent')
    - expect: Returns empty string

#### 4.6. Search memory for semantically similar items

**File:** `tests/memory-system-tests/memory-manager-semantic-search.spec.ts`

**Steps:**
  1. Given MemoryManager with VectorStore containing items about user preferences
    - expect: VectorStore has items
  2. When calling semantic_search('programming', n_results=3)
    - expect: Returns list of matching item IDs
    - expect: Results sorted by relevance (distance)
  3. When calling semantic_search() with default n_results
    - expect: Returns up to 5 results

### 5. API Integration

**Seed:** `tests/seed.spec.ts`

#### 5.1. POST /api/chat stores messages in memory

**File:** `tests/memory-system-tests/api-chat-memory.spec.ts`

**Steps:**
  1. Given FastAPI server running with ConversationManager
    - expect: Server is accessible at http://127.0.0.1:8001
  2. When POST /api/sessions with title='Test Session'
    - expect: Returns 201 with session_id and title
  3. When POST /api/chat with session_id, message='My name is Charlie'
    - expect: Returns 200 with response
    - expect: User message stored in session memory
    - expect: Assistant response stored in session memory
  4. When GET /api/sessions/{session_id}
    - expect: Returns session with both messages in messages array
    - expect: Messages have correct roles and content

#### 5.2. Session detail includes full message history

**File:** `tests/memory-system-tests/api-session-detail.spec.ts`

**Steps:**
  1. Given a session with 5 messages exchanged
    - expect: Session exists with messages
  2. When GET /api/sessions/{session_id}
    - expect: Returns 200 with session details
    - expect: Response includes session_id, title, created_at, updated_at
    - expect: Response includes messages array with all 5 messages
    - expect: Each message has role, content, created_at

#### 5.3. Short-term and long-term memory survive server restart

**File:** `tests/memory-system-tests/api-persistence.spec.ts`

**Steps:**
  1. Given server running with session 'session-1' containing messages and profile 'owner' with name='Dave'
    - expect: Data persisted to JSON files and ChromaDB
  2. When server is restarted
    - expect: Server starts successfully
  3. When GET /api/sessions/{session_id} after restart
    - expect: Returns session with all previous messages
  4. When MemoryManager.get_user_profile('owner') after restart
    - expect: Returns profile with name='Dave'
  5. When VectorStore.get_all_items() after restart
    - expect: Returns previously stored items

#### 5.4. Multiple sessions operate independently

**File:** `tests/memory-system-tests/api-concurrent-sessions.spec.ts`

**Steps:**
  1. Given server running
    - expect: Server is accessible
  2. When creating session-1 and session-2 via POST /api/sessions
    - expect: Both sessions created with unique IDs
  3. When sending messages to session-1: 'I like cats'
    - expect: Message stored in session-1
  4. When sending messages to session-2: 'I prefer dogs'
    - expect: Message stored in session-2
  5. When GET /api/sessions/{session-1}
    - expect: Returns only session-1 messages (cats)
  6. When GET /api/sessions/{session-2}
    - expect: Returns only session-2 messages (dogs)

### 6. Frontend Behavior

**Seed:** `tests/seed.spec.ts`

#### 6.1. Chat history loads correctly from memory

**File:** `tests/memory-system-tests/frontend-chat-history.spec.ts`

**Steps:**
  1. Given frontend loaded at http://127.0.0.1:8001 with existing session containing messages
    - expect: Page loads without errors
  2. When clicking on existing session in conversation list
    - expect: Session opens
    - expect: Messages display in correct order with roles
    - expect: User messages show 'Você' label
    - expect: Assistant messages show 'J.A.R.V.I.S.' label
  3. When sending new message
    - expect: Message appears in chat
    - expect: Response appears after processing
    - expect: Both messages persist in session

#### 6.2. New session has no previous messages

**File:** `tests/memory-system-tests/frontend-new-session.spec.ts`

**Steps:**
  1. Given frontend with existing session containing messages
    - expect: Current session shows messages
  2. When clicking 'Nova conversa' button
    - expect: New session created
    - expect: Chat area shows empty state 'Como posso ajudar?'
    - expect: No previous messages visible
  3. When sending first message in new session
    - expect: Message sent successfully
    - expect: Response received
    - expect: Session title updates from message content

#### 6.3. Long-term profile persists across frontend sessions

**File:** `tests/memory-system-tests/frontend-profile-persistence.spec.ts`

**Steps:**
  1. Given user has profile with name='Eve' stored in long-term memory
    - expect: Profile exists in long_term.json
  2. When opening frontend in new browser tab
    - expect: Frontend loads
  3. When creating new session and asking 'What is my name?'
    - expect: Assistant responds with knowledge of user's name from long-term profile

#### 6.4. Memory operations are transparent to user

**File:** `tests/memory-system-tests/frontend-transparent-memory.spec.ts`

**Steps:**
  1. Given frontend loaded
    - expect: No memory management UI elements visible
    - expect: No buttons for 'save memory', 'clear memory', 'view profile'
  2. When using chat normally
    - expect: Memory operations happen automatically in background
    - expect: User experiences seamless conversation with context
