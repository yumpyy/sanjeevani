import base64

import httpx
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def create_description(image_data, model=gemini):
    """
    generates a detailed and structured medical description of an image.

    args:
        image_data (str): base64-encoded image data
        model: a language model capable of processing multimodal input (text and images)

    returns:
        str: a comprehensive textual description of the medical details in the image
    """

    prompt = """
    Generate an extremely detailed and comprehensive textual description of all visible medical details in the provided image, ensuring that a doctor could assess the patient's condition without needing to see the image. The description must be exhaustive, medically precise, and structured as follows:  

    1. **General Information**  
       - **Body Part & Orientation:** Identify the specific body part(s) visible in the image and its orientation (e.g., anterior/posterior, left/right, dorsal/ventral).  
       - **Skin & Tissue Condition:** Describe the texture, color, tone, elasticity, and presence of any abnormalities such as rashes, inflammation, or lesions.  
       - **Visible Circulatory or Nervous Features:** Note the visibility of veins, arteries, or nerves if relevant, including any abnormal bulging, discoloration, or pattern changes.  
       - **Hair & Nails (if applicable):** Describe the density, texture, color, brittleness, or presence of any abnormalities in hair and nails.  

    2. **Specific Conditions & Lesions**  
       For any identified condition, include:  
       - **Type & Classification:** Define whether it is a wound, rash, ulcer, lesion, infection, or other pathology.  
       - **Size & Shape:** Provide exact dimensions (length, width, depth in mm/cm), shape (linear, circular, irregular), and spread pattern.  
       - **Color Variations:** Describe pigmentation, redness, pallor, bruising, or other discolorations.  
       - **Texture & Surface Features:** Indicate if the area is raised, sunken, crusted, oozing, scabbed, or peeling.  
       - **Fluid Presence:** Specify any bleeding (amount, rate, clotting status), pus (color, viscosity, presence of odor), or clear fluid discharge.  
       - **Signs of Infection:** Note redness, swelling, warmth, pus formation, foul odor, or spreading streaks.  
       - **Pain Indicators:** If visually assessable (e.g., grimacing, guarding behavior), describe signs of pain or tenderness.  

    3. **Specific Diagnoses & Indicators**  
       For common conditions, provide the following details:  
       - **Cuts, Scratches, or Lacerations:** Length, depth, active bleeding, clot formation, infection signs, surrounding tissue reaction.  
       - **Burns:** Degree (1st, 2nd, 3rd), area affected (percentage of body surface), blistering, charring, eschar formation.  
       - **Bruises (Ecchymosis or Hematoma):** Color (red, purple, yellow, green stages), size, swelling, tenderness.  
       - **Rashes (Eczema, Psoriasis, Chickenpox, Measles, etc.):** Distribution, lesion type (papules, pustules, vesicles), itching, scaling, crusting.  
       - **Mouth Ulcers:** Location, depth, color, surrounding inflammation, presence of pus or necrosis.  
       - **Nail Abnormalities (Fungal Infections, Clubbing, Beau’s Lines, etc.):** Thickness, discoloration, texture, detachment.  

    4. **Additional Systemic Signs**  
       - **Swelling & Edema:** Note location, pitting or non-pitting, associated redness or warmth.  
       - **Temperature Differences:** Identify any hot or cold areas that might suggest infection or vascular compromise.  
       - **Muscle or Joint Deformities:** Visible swelling, abnormal positioning, asymmetry, dislocations.  
       - **Neurological Signs:** Muscle atrophy, tremors, involuntary movements, rigidity.  

    5. **Background & Environment (if visible)**  
       - **Cleanliness & Hygiene Indicators:** Presence of dirt, sweat, poor hygiene factors.  
       - **Bandages or Medical Devices:** Condition, placement, soiling, effectiveness of wound coverage.  
       - **External Objects:** Presence of foreign bodies embedded in the wound or skin.  

    **Provide only the analysis. Do not include explanations or recommendations.**
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )
    response = model.invoke([message])

    return response.content

def bleh(model):
    image_url = "https://i.ibb.co/TxM1j509/IMG-20250216-133400-333.jpg"
    image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
    return create_description(image_data, model)
