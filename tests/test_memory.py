from jarvis.memory import MemoryStore


def test_short_term_memory_tracks_recent_context(tmp_path):
    memory = MemoryStore(storage_dir=tmp_path)

    memory.remember("session-1", "user", "Meu nome é João")
    memory.remember("session-1", "assistant", "Olá, João!")

    context = memory.recall("session-1")

    assert "Meu nome é João" in context
    assert "Olá, João!" in context


def test_long_term_memory_persists_user_profile(tmp_path):
    first_store = MemoryStore(storage_dir=tmp_path)
    first_store.save_profile(
        "owner",
        {
            "name": "João",
            "preferences": ["resumos curtos", "linguagem direta"],
        },
    )

    second_store = MemoryStore(storage_dir=tmp_path)
    profile = second_store.get_profile("owner")

    assert profile["name"] == "João"
    assert "resumos curtos" in profile["preferences"]


def test_user_profile_merges_preferences_and_facts(tmp_path):
    memory = MemoryStore(storage_dir=tmp_path)

    memory.save_profile(
        "owner",
        {
            "name": "João",
            "preferences": ["resumos curtos"],
            "facts": ["Prefere respostas diretas"],
        },
    )
    memory.save_profile(
        "owner",
        {
            "preferences": ["resumos curtos", "linguagem direta"],
            "facts": ["Prefere respostas diretas", "Gosta de listas curtas"],
        },
    )

    profile = memory.get_profile("owner")

    assert profile["name"] == "João"
    assert "resumos curtos" in profile["preferences"]
    assert profile["preferences"].count("resumos curtos") == 1
    assert "linguagem direta" in profile["preferences"]
    assert "Prefere respostas diretas" in profile["facts"]
    assert profile["facts"].count("Prefere respostas diretas") == 1
    assert "Gosta de listas curtas" in profile["facts"]


def test_search_history_finds_relevant_context(tmp_path):
    memory = MemoryStore(storage_dir=tmp_path)

    memory.remember("session-1", "user", "Meu nome é João")
    memory.remember("session-1", "assistant", "Vou usar respostas curtas.")
    memory.remember("session-1", "user", "Prefiro linguagem direta")

    results = memory.search_history("session-1", "curtas")

    assert results
    assert any("curtas" in item.lower() for item in results)


def test_search_history_ignores_empty_query(tmp_path):
    memory = MemoryStore(storage_dir=tmp_path)
    memory.remember("session-1", "user", "Texto de exemplo")

    assert memory.search_history("session-1", "") == []
    assert memory.search_history("session-1", "   ") == []
