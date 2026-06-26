SYSTEM_PROMPT = """
You are DocuMind AI, a professional document analysis assistant.
Use only the provided document context when answering document-based questions.
If the answer is not available in the context, say that clearly.
Keep answers clear, structured, and helpful for students and professionals.
"""

QA_PROMPT = """
Question: {question}

Relevant document context:
{context}

Answer with:
1. Direct answer
2. Supporting points from documents
3. Source references using file names and chunk numbers
"""

SUMMARY_PROMPT = """
Create a {style} summary of the following document content.
Include key ideas, important terms, and conclusions.

Content:
{context}
"""

COMPARE_PROMPT = """
Compare these documents based on the available content.
Discuss similarities, differences, strengths, weaknesses, and final recommendation.

Content:
{context}
"""

QUIZ_PROMPT = """
Generate a quiz from this document content.
Create {num_questions} questions with answers.
Include a mix of MCQs and short questions.

Content:
{context}
"""

FLASHCARD_PROMPT = """
Generate revision flashcards from this content.
Format each as:
Q: ...
A: ...

Content:
{context}
"""
