from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from config import get_llm

load_dotenv()


def _model():
    """Build a vision-capable chat model. The model name in
    ``OPENAI_MODEL`` must support image inputs (e.g. gpt-4o, gpt-4-vision,
    or a self-hosted equivalent that the OpenAI-compatible endpoint
    exposes as vision)."""
    return get_llm()


def create_description(image_data: str) -> str:
    """
    Generates a detailed and structured medical description of an image.

    Args:
        image_data: base64-encoded image data (without the
            "data:image/jpeg;base64," prefix).

    Returns:
        A comprehensive textual description of the medical details in the
        image, or a short skip-message if the API key is missing.
    """
    try:
        model = _model()
    except RuntimeError as e:
        print(f"Image analysis skipped: {e}")
        return "Image analysis skipped due to missing API key."

    if image_data.startswith("data:image"):
        image_url_content = image_data
    else:
        image_url_content = f"data:image/jpeg;base64,{image_data}"

    prompt = """
    Generate an extremely detailed and comprehensive textual description of all visible medical details in the provided image, ensuring that a doctor could assess the patient's condition without needing to see the image. Focus on objective observations and use precise medical terminology where appropriate. Structure the description as follows:

    **OBSERVATION:**

    1.  **General Description:**
        -   Body Part & Orientation: Identify the specific body part(s) visible and its orientation (e.g., anterior/posterior view of left forearm).
        -   Overall Appearance: Describe the general condition of the visible area.

    2.  **Detailed Findings:** Describe any abnormalities or points of interest. Be specific regarding:
        -   **Lesion/Area Type:** Is it a rash, wound, swelling, bruise, lesion, etc.?
        -   **Location & Distribution:** Exact location on the body part, is it localized or widespread?
        -   **Size & Shape:** Estimated size (mm/cm), specific shape (circular, irregular, linear).
        -   **Color:** Detailed description of colors present (red, purple, pale, jaundiced, pigmented variations).
        -   **Texture & Surface:** Is it raised, flat, sunken, smooth, rough, scaly, crusted, oozing, blistering?
        -   **Edges/Margins:** Are they well-defined or irregular?
        -   **Fluid/Discharge:** Presence, type (serous, purulent, sanguineous), amount, consistency, odor (if inferable from visual signs like pus color/texture).
        -   **Signs of Inflammation/Infection:** Redness (erythema), swelling (edema), warmth (if visual indicators like prominent veins/flush), streaks (lymphangitis).
        -   **Integrity:** Is the skin intact? Are there breaks, cuts, abrasions?
        -   **Underlying Structures:** Visibility or apparent condition of veins, tendons, bones, muscles if relevant.

    3.  **Additional Relevant Visual Cues:**
        -   Presence of old scars, previous lesions, or other dermatological findings.
        -   Condition of surrounding skin.
        -   Presence of bandages, dressings, or foreign objects (describe them objectively).
        -   Hygiene indicators visible in the immediate area.

    **INSTRUCTIONS:**
    -   Provide ONLY the objective medical description under the "OBSERVATION:" heading.
    -   DO NOT include diagnosis, interpretation, prognosis, or recommendations.
    -   Maintain a clinical, objective tone.
    -   Be as specific and quantitative as possible based *only* on visual evidence.
    """
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": image_url_content},
            },
        ],
    )
    try:
        response = model.invoke([message])
        return response.content
    except Exception as e:
        print(f"Error invoking image analysis model: {e}")
        return f"Error analyzing image: {e}"
