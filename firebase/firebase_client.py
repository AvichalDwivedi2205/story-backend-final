import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

load_dotenv()

class FirebaseClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            try:
                cred_path = os.getenv("FIREBASE_CREDENTIALS")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                cls._instance.db = firestore.client()
                print("Firebase initialized successfully")
            except Exception as e:
                print(f"Firebase initialization error: {e}")
                cls._instance = None
        return cls._instance

    def save_journal_entry(self, user_id, journal_data):
        """Save journal entry with analysis to Firebase"""
        try:
            # Convert datetime objects to ISO format strings
            journal_data["journal_entry"]["timestamp"] = journal_data["journal_entry"]["timestamp"].isoformat()

            # Save to journal collection
            journal_ref = self.db.collection("journal").document()
            journal_ref.set({
                "user_id": user_id,
                "content": journal_data["journal_entry"]["content"],
                "timestamp": journal_data["journal_entry"]["timestamp"],
                "sentiment": journal_data["sentiment_analysis"],
                "emotion": journal_data["emotion_analysis"],
                "insights": journal_data["insights"],
            })
            return journal_ref.id
        except Exception as e:
            print(f"Error saving journal entry: {e}")
            return None

    def save_exercises(self, user_id, exercises):
        """Save or update exercises for a user"""
        try:
            # Format exercises for Firebase
            exercise_data = {
                "morning_reflection": exercises.morning_reflection.dict(),
                "gratitude_exercise": exercises.gratitude_exercise.dict(),
                "mindfulness_meditation": exercises.mindfulness_meditation.dict(),
                "cbt_exercise": exercises.cbt_exercise.dict(), 
                "relaxation_techniques": exercises.relaxation_techniques.dict(),
                "last_updated": datetime.now().isoformat()
            }

            # Update user exercises
            user_ref = self.db.collection("users").document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_ref.update({"exercises": exercise_data})
            else:
                user_ref.set({"exercises": exercise_data})
                
            return True
        except Exception as e:
            print(f"Error saving exercises: {e}")
            return False

    def save_therapy_session(self, therapy_session):
        """Save therapy conversation and summary to Firebase"""
        try:
            # Convert messages timestamp to string
            messages = []
            for msg in therapy_session.messages:
                messages.append({
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "is_user": msg.is_user
                })
                
            # Save to chatbot collection
            chat_ref = self.db.collection("chatbot").document()
            chat_ref.set({
                "user_id": therapy_session.user_id,
                "timestamp": therapy_session.timestamp.isoformat(),
                "messages": messages,
                "session_summary": therapy_session.session_summary
            })
            return chat_ref.id
        except Exception as e:
            print(f"Error saving therapy session: {e}")
            return None

    def get_user_journal_entries(self, user_id, limit=5):
        """Get recent journal entries for a user"""
        try:
            entries = []
            query = (self.db.collection("journal")
                     .where("user_id", "==", user_id)
                     .order_by("timestamp", direction=firestore.Query.DESCENDING)
                     .limit(limit))
            
            docs = query.stream()
            for doc in docs:
                entry = doc.to_dict()
                entry["id"] = doc.id
                entries.append(entry)
                
            return entries
        except Exception as e:
            print(f"Error retrieving journal entries: {e}")
            return []

    def get_user_exercises(self, user_id):
        """Get exercises for a user"""
        try:
            user_ref = self.db.collection("users").document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists and "exercises" in user_doc.to_dict():
                return user_doc.to_dict()["exercises"]
            return None
        except Exception as e:
            print(f"Error retrieving exercises: {e}")
            return None

    def save_workflow_plan(self, workflow_data):
        """Save workflow plan to Firebase"""
        try:
            # Convert datetime objects to ISO format strings
            workflow_data["timestamp"] = workflow_data["timestamp"].isoformat()
            
            # Save to workflows collection
            workflow_ref = self.db.collection("workflows").document()
            workflow_ref.set(workflow_data)
            return workflow_ref.id
        except Exception as e:
            print(f"Error saving workflow plan: {e}")
            return None