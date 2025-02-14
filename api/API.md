# **Sanjeevani API Documentation**  

## **Base URL**  
```
https://example.com/
```

---

## **Endpoints**

### **1. Get Available Doctors**  
Retrieve a list of doctor types supported by the API.

#### **Endpoint**  
```http
GET /doctors/
```

#### **Response**  
```json
{
  "available_doctors": ["physician", "therapist"]
}
```

---

### **2. Start a Diagnosis Session**  
Begins a **new medical diagnosis** session with a selected doctor.

#### **Endpoint**  
```http
POST /diagnosis/{doctor_id}/
```

#### **Path Parameter**  
| Parameter   | Type   | Description                                  |
|------------|--------|----------------------------------------------|
| `doctor_id` | `string` | Type of doctor (`physician` or `therapist`) |

#### **Request Body**  
```json
{
  "age": 30,
  "sex": "male",
  "symptoms": "fever, cough, body ache"
}
```

#### **Response**  
If further clarification is needed:
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "diagnosis_complete": false,
  "question": "How long have you been experiencing fever?"
}
```

If no further clarification is needed:
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "diagnosis_complete": true,
  "prescription": {
    "recommend_medicines": ["Paracetamol 500mg"],
    "dosage": "Take one tablet every 6 hours after food",
    "potential_side_effects": ["Nausea", "Dizziness"],
    "contraindications": ["Liver disease"],
    "alternative_treatments": ["Drink warm fluids, Rest"],
    "emergency_advice": "Consult a doctor if fever persists for more than 3 days",
    "consultation_required": false
  }
}
```

---

### **3. Continue Diagnosis**  
Sends answers to previous clarification questions and gets the next question if needed.

#### **Endpoint**  
```http
POST /diagnosis/{session_id}/continue
```

#### **Path Parameter**  
| Parameter   | Type   | Description                  |
|------------|--------|------------------------------|
| `session_id` | `string` | Unique session identifier |

#### **Request Body**  
```json
{
  "clarification_questions": {
    "How long have you been experiencing fever?": "2 days"
  }
}
```

#### **Response**  
If more clarification is needed:
```json
{
  "diagnosis_complete": false,
  "question": "Do you have any underlying health conditions?"
}
```

If diagnosis is complete:
```json
{
  "diagnosis_complete": true,
  "prescription": {
    "recommend_medicines": ["Paracetamol 500mg"],
    "dosage": "Take one tablet every 6 hours after food",
    "potential_side_effects": ["Nausea", "Dizziness"],
    "contraindications": ["Liver disease"],
    "alternative_treatments": ["Drink warm fluids, Rest"],
    "emergency_advice": "Consult a doctor if fever persists for more than 3 days",
    "consultation_required": false
  }
}
```

---

### **4. Get Clarification History**  
Retrieves all previous clarification questions and answers in a session.

#### **Endpoint**  
```http
GET /diagnosis/{session_id}/history
```

#### **Path Parameter**  
| Parameter   | Type   | Description                  |
|------------|--------|------------------------------|
| `session_id` | `string` | Unique session identifier |

#### **Response**  
```json
{
  "clarification_history": {
    "How long have you been experiencing fever?": "2 days",
    "Do you have any underlying health conditions?": "No"
  }
}
```

---

### **5. Get Prescription**  
Retrieves the final prescription if the diagnosis is complete.

#### **Endpoint**  
```http
GET /diagnosis/{session_id}/prescription
```

#### **Path Parameter**  
| Parameter   | Type   | Description                  |
|------------|--------|------------------------------|
| `session_id` | `string` | Unique session identifier |

#### **Response**  
```json
{
  "prescription": {
    "recommend_medicines": ["Paracetamol 500mg"],
    "dosage": "Take one tablet every 6 hours after food",
    "potential_side_effects": ["Nausea", "Dizziness"],
    "contraindications": ["Liver disease"],
    "alternative_treatments": ["Drink warm fluids, Rest"],
    "emergency_advice": "Consult a doctor if fever persists for more than 3 days",
    "consultation_required": false
  }
}
```
