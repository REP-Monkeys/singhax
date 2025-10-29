@echo off
echo Running LangGraph Conversation Tests...
python scripts/test_conversation.py happy_path
echo.
echo.
echo Running No Adventure Sports Test...
python scripts/test_conversation.py no_adventure_sports
pause

