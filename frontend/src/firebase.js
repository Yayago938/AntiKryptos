// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyAojQS5o7eMXD2vqgoqlTCKxDvvCVO_Y60",
  authDomain: "keshackathon.firebaseapp.com",
  projectId: "keshackathon",
  storageBucket: "keshackathon.firebasestorage.app",
  messagingSenderId: "81454232410",
  appId: "1:81454232410:web:5ed92158636105e218b963"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();