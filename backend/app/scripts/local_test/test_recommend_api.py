import json
import urllib.request

API_URL = "http://localhost:8000/recommend"

def post_recommend(query: str, top_k: int = 5) -> dict:
    payload = {
        "user_id": "test_user",
        "query": query,
        "top_k": top_k,
    }
    
    data = json.dumps(payload).encode("utf-8") # Convert payload to JSON and encode as bytes for the POST request

    request = urllib.request.Request( # Create POST request to the recommendation API
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response: # Send POST request to the API
        response_data = response.read().decode("utf-8")
        return json.loads(response_data)
    
def main():
    queries = [
        "lonely gentle futuristic romance like Her",
        "dark psychological thriller with mystery",
        "funny animated family adventure",
        "epic fantasy movie with magic and battles",
    ]
    for query in queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")

        response = post_recommend(query=query, top_k=3)
        print(f"Latency: {response['latency_ms']} ms")

        for rank, movie in enumerate(response["results"], start=1):
            print(
                f"{rank}. {movie['title']} "
                f"({movie['release_year']}) "
                f"[score={movie['score']}] "
                f"[genres={movie['genres']}]"
            )


if __name__ == "__main__":
    main()