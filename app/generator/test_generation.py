import logging
from app.generator.rag_pipeline import ask_rag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("test_generation")

def main():
    print("\n" + "=" * 100)
    print("SRM CampusGPT - RAG Test")
    print("=" * 100)
    print("Type 'exit' or 'quit' to stop\n")

    while True:
        try:
            query = input("\n🔍 Ask a question: ").strip()

            if not query:
                print("❌ Please enter a valid question")
                continue

            if query.lower() in ["exit", "quit"]:
                print("\n👋 Goodbye!")
                break

            print("\n⏳ Processing...\n")

            result = ask_rag(query)

            if not result:
                print("❌ Error: No result returned")
                continue

            answer = result.get("answer", "")
            confidence = result.get("confidence", 0)
            confidence_label = result.get("confidence_label", "Unknown")
            response_time = result.get("response_time", 0)
            docs_info = result.get("docs_info", [])

            if not answer:
                print("❌ Error: Empty answer returned")
                continue

            print("\n" + "=" * 100)
            print("ANSWER")
            print("=" * 100)
            print(answer)
            print("=" * 100)

            print(f"\n📊 Confidence: {confidence}% ({confidence_label})")
            print(f"⏱️  Response Time: {response_time}s")

            if docs_info:
                print(f"\n📚 Sources ({len(docs_info)} docs):\n")
                for i, doc in enumerate(docs_info[:5], 1):
                    source = doc.get("source", "unknown")
                    distance = doc.get("distance", "N/A")
                    chunk_id = doc.get("chunk_id", "unknown")
                    print(f"  {i}. Source: {source} | Distance: {distance} | ID: {chunk_id[:50]}")
            else:
                print("\n⚠️  No sources found")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            print(f"❌ Error: {str(e)}")
            print("Please try another question\n")

if __name__ == "__main__":
    main()