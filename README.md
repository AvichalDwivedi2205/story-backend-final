# Story.AI: Mental Well-Being AI Agents

Story.AI is a comprehensive mental well-being platform powered by specialized AI agents implemented with Fetch.AI's uAgents framework and registered on Agentverse. These agents work together to provide personalized support for users' mental health needs.

## Architecture

The system consists of these specialized AI agents:

1. **Journal Analysis Agent**: Analyzes journal entries using sentiment and emotion detection models, generates therapeutic insights, and triggers exercise generation.

2. **Exercise Generator Agent**: Creates customized morning reflection and CBT exercises based on journal insights.

3. **Gratitude Agent**: Helps users recognize positive aspects in life through personalized gratitude exercises.

4. **Therapy Conversation Agent**: Provides context-aware AI therapy sessions with conversational memory and session summaries.

5. **Story.AI Guide Agent**: Helps users navigate the platform's features and suggests relevant activities.

6. **Personalized Assistant Agent**: Acts as a central hub, dynamically connecting with other agents to fulfill user queries.

## Technology Stack

- Backend Framework: FastAPI
- AI Integration: Gemini API via Google Generative AI
- Database: Firebase (Firestore)
- Agent Framework: Fetch.AI uAgents + Agentverse
- NLP Models: 
  - `cardiffnlp/twitter-roberta-base-sentiment` for sentiment analysis
  - `j-hartmann/emotion-english-distilroberta-base` for emotion analysis
- Conversational AI: LangChain + Gemini

## Setup and Installation

1. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   - Ensure your `.env` file contains the necessary API keys (see `.env.example`).
   - Make sure your Firebase credentials file path is correctly set.

3. **Run the application**:
   ```
   python app.py
   ```

4. **API Documentation**:
   - Once running, Swagger documentation is available at `http://localhost:8000/docs`

## Agent Interaction Flow

1. **Journal Flow**: User writes a journal entry → Journal Analysis Agent processes it → Exercise Generator Agent creates exercises → Gratitude Agent creates a gratitude practice.

2. **Therapy Flow**: User starts a therapy session → Therapy Agent maintains conversation context → At the end, a session summary is generated.

3. **Guidance Flow**: User asks what to do → Assistant Agent routes to Guide Agent → Guide Agent recommends features and potentially external agents.

## API Endpoints

### Journal API
- `POST /api/journal/analyze`: Submit a journal entry for analysis

### Exercise API
- `POST /api/exercise/generate`: Generate personalized exercises

### Gratitude API
- `POST /api/gratitude/generate`: Generate a gratitude exercise

### Therapy API
- `POST /api/therapy/session`: Handle therapy sessions (start, continue, end)

### Guide API
- `POST /api/guide/recommend`: Get personalized feature recommendations

### Assistant API
- `POST /api/assistant/query`: Process a user query and route to appropriate agents

## Agentverse Integration

All agents are registered with Agentverse, allowing them to interact with other agents in the ecosystem. The Personalized Assistant Agent can search and discover relevant agents on Agentverse to provide comprehensive support.