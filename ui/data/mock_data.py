"""
Temporary mock data.

Future:
Replace these functions with database/service calls.
"""


def get_mock_chats():
    """
    Temporary chat history.

    Future:
    Replace with:
    database.get_user_chats(user_id)
    """

    return [
        "شرایط دریافت مجوز نیروگاه",
        "تعرفه برق صنعتی",
        "قوانین اتصال به شبکه"
    ]


def get_mock_response():
    """
    Temporary AI response.

    Future:
    Replace with:

    response = chat_service.ask(question)

    Expected backend output:
    {
        answer: str,
        sources: list,
        scores: dict,
        suggestions: list,
        metadata: dict
    }
    """

    return {

        # -------------------------------------------------
        # ANSWER
        # -------------------------------------------------

        "answer": "این یک پاسخ آزمایشی است.",


        # -------------------------------------------------
        # SOURCES
        # -------------------------------------------------

        "sources": [
            {
                "title": "آیین نامه نیروگاه",
                "page": 12,
                "content": "بخش مربوط به شرایط دریافت مجوز"
            }
        ],


        # -------------------------------------------------
        # EVALUATION SCORES
        # -------------------------------------------------

        "scores": {
            "relevance": 0.86,
            "completeness": 0.78,
            "faithfulness": 0.93
        },


        # -------------------------------------------------
        # SUGGESTED QUESTIONS
        # -------------------------------------------------

        "suggestions": [
            "مدارک لازم برای دریافت مجوز چیست؟",
            "مراحل دریافت مجوز نیروگاه چگونه است؟",
            "هزینه دریافت مجوز نیروگاه چقدر است؟"
        ],


        # -------------------------------------------------
        # METADATA
        # -------------------------------------------------

        "metadata": {
            "retrieval_time": "1.2s",
            "model": "mock-model",
            "documents_used": 3
        }
    }