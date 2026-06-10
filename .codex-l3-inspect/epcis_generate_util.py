import os
import json
from datetime import datetime
from generator import EPICSGenerator


def generate_epcis_xml_from_json(json_path, output_dir="EPCISfiles"):
    """
    Loads the input JSON, generates EPCIS XML using EPICSGenerator, and saves the XML file.
    Args:
        json_path (str): Path to the input JSON file.
        output_dir (str): Directory to save the generated XML file.
    Returns:
        str: Path to the generated XML file.
    Raises:
        Exception: If any error occurs during the process.
    """
    import os
    import json
    from datetime import datetime

    try:
        from .generator import EPICSGenerator
    except Exception:
        from generator import EPICSGenerator


    def generate_epcis_xml_from_json(json_path, output_dir="EPCISfiles"):
        """
        Loads the input JSON, generates EPCIS XML using EPICSGenerator, and saves the XML file.
        Args:
            json_path (str): Path to the input JSON file.
            output_dir (str): Directory to save the generated XML file.
        Returns:
            str: Path to the generated XML file.
        Raises:
            Exception: If any error occurs during the process.
        """
        # Load input data
        with open(json_path, "r") as f:
            data = json.load(f)

        # Create generator object
        generator = EPICSGenerator(data)

        # Generate the full EPCIS document (not just header)
        xml_root = generator.generate_epcis_document()

        # Convert XML tree to string
        import xml.etree.ElementTree as ET
        xml_str = ET.tostring(xml_root, encoding="utf-8", method="xml").decode("utf-8")

        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save XML to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        xml_filename = f"epcis_{timestamp}.xml"
        xml_path = os.path.join(output_dir, xml_filename)
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
import os
import json
from datetime import datetime

try:
    from .generator import EPICSGenerator
except Exception:
    from generator import EPICSGenerator


def generate_epcis_xml_from_json(basic_data, json_path, output_dir="EPCISfiles"):
    """
    Loads the input JSON, generates EPCIS XML using EPICSGenerator, and saves the XML file.
    Args:
        json_path (str): Path to the input JSON file.
        output_dir (str): Directory to save the generated XML file.
    Returns:
        str: Path to the generated XML file.
    Raises:
        Exception: If any error occurs during the process.
    """
    if not json_path or not isinstance(json_path, str):
        raise ValueError("json_path must be a valid file path string")

    # Load input data
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create generator object
    generator = EPICSGenerator(data)

    # Generate the full EPCIS document (not just header)
    xml_root = generator.generate_epcis_document()

    # Convert XML tree to string
    import xml.etree.ElementTree as ET
    xml_str = ET.tostring(xml_root, encoding="utf-8", method="xml").decode("utf-8")

    # Normalize output_dir
    if not output_dir or not isinstance(output_dir, str):
        output_dir = os.path.join(os.getcwd(), "EPCISfiles")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Save XML to file
    timestamp = datetime.now().strftime("%H%M%S")
    xml_filename = f"EPCIS_{basic_data.get('lot_number', '')}_{timestamp}.xml"
    xml_path = os.path.join(output_dir, xml_filename)
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

    return xml_path
