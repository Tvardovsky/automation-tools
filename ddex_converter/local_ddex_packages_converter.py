from lxml import etree
import os
import shutil
import hashlib
from datetime import datetime
from PIL import Image

def deep_copy_element(source_element, target_element):
    """Copy the content of source element to target element, preserving the structure."""
    for sub_element in source_element:
        new_sub_element = etree.SubElement(target_element, sub_element.tag, sub_element.attrib)
        if sub_element.text and sub_element.text.strip():
            new_sub_element.text = sub_element.text.strip()
        deep_copy_element(sub_element, new_sub_element)
        if sub_element.tail and sub_element.tail.strip():
            new_sub_element.tail = sub_element.tail.strip()

def update_message_recipient(root):
    """Update the MessageRecipient section with the new data."""
    for message_recipient_element in root.xpath('//MessageRecipient'):
        party_id_element = message_recipient_element.find('.//PartyId')
        if party_id_element is not None:
            party_id_element.text = 'PADPIDA2021092801S'
            if 'Namespace' in party_id_element.attrib:
                del party_id_element.attrib['Namespace']
        
        party_name_element = message_recipient_element.find('.//PartyName')
        if party_name_element is not None:
            full_name_element = party_name_element.find('.//FullName')
            if full_name_element is not None:
                full_name_element.text = 'BeatData.Pro, LLC'

def update_icpn(root, ean_upc_code):
    """Update the ICPN section with new data."""
    for icpn_element in root.xpath('//ICPN'):
        if icpn_element.text:
            icpn_element.set('IsEan', 'true')
            icpn_element.text = ean_upc_code

def upscale_image(image_path):
    """Upscale image to 3000x3000 if it's smaller."""
    try:
        with Image.open(image_path) as img:
            if img.width < 3000 or img.height < 3000:
                img = img.resize((3000, 3000), Image.LANCZOS)
                img.save(image_path)
                print(f"Upscaled image saved at: {image_path}")
    except Exception as e:
        print(f"Error upscaling image {image_path}: {e}")

def calculate_md5(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def update_image_metadata_and_hash(root, resources_folder):
    """Update image metadata and hash for upscaled images."""
    for file_element in root.xpath('//File'):
        file_name_element = file_element.find('FileName')
        file_path_element = file_element.find('FilePath')
        if file_name_element is not None and file_path_element is not None:
            image_path = os.path.join(resources_folder, file_name_element.text)
            if os.path.exists(image_path):
                if image_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    upscale_image(image_path)
                    new_hash = calculate_md5(image_path)
                    hash_sum_element = file_element.find('HashSum/HashSum')
                    if hash_sum_element is not None:
                        hash_sum_element.text = new_hash

def convert_ddex_structure(input_xml_path, output_xml_path, resources_folder, ean_upc_code):
    """Convert the structure of the DDEX XML."""
    if not os.path.exists(input_xml_path) or os.path.getsize(input_xml_path) == 0:
        print(f"Error: The file {input_xml_path} does not exist or is empty.")
        return None

    try:
        tree = etree.parse(input_xml_path)
    except etree.XMLSyntaxError as e:
        print(f"Error parsing XML file {input_xml_path}: {e}")
        return None

    root = tree.getroot()
    ns = root.nsmap
    new_nsmap = {'ern': 'http://ddex.net/xml/ern/382', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    new_root = etree.Element(
        '{http://ddex.net/xml/ern/382}NewReleaseMessage',
        nsmap=new_nsmap,
        attrib={
            'LanguageAndScriptCode': 'en',
            '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation': 'http://ddex.net/xml/ern/382 http://ddex.net/xml/ern/382/release-notification.xsd',
            'MessageSchemaVersionId': 'ern/382'
        }
    )
    
    sections = ['MessageHeader', 'UpdateIndicator', 'ResourceList', 'ReleaseList', 'DealList']
    
    for section in sections:
        section_path = f'{{{ns["ern"]}}}{section}'
        source_element = root.find(section_path)
        if source_element is not None:
            new_element = etree.SubElement(new_root, section, source_element.attrib)
            deep_copy_element(source_element, new_element)
        else:
            source_element = root.find(section)
            if source_element is not None:
                new_element = etree.SubElement(new_root, section, source_element.attrib)
                deep_copy_element(source_element, new_element)
            else:
                print(f"Section {section} not found in input XML.")

    update_message_recipient(new_root)
    update_image_metadata_and_hash(new_root, resources_folder)
    update_icpn(new_root, ean_upc_code)

    new_tree = etree.ElementTree(new_root)
    new_tree.write(output_xml_path, encoding='utf-8', xml_declaration=True, pretty_print=True)
    return output_xml_path

def copy_resources(src_folder, dst_folder):
    """Copy resource files from the source folder to the destination folder."""
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
    for item in os.listdir(src_folder):
        s = os.path.join(src_folder, item)
        d = os.path.join(dst_folder, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, False, None)
        else:
            shutil.copy2(s, d)

def create_batch_complete_xml(output_folder, batch_folder, package_folders, xml_file_names, message_ids, icpns, hash_sums):
    """Create the BatchComplete XML file."""
    batch_complete_path = os.path.join(output_folder, batch_folder, f'BatchComplete_{batch_folder}.xml')

    new_nsmap = {
        'ern-c-sftp': 'http://ddex.net/xml/ern-c-sftp/16',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'avs': 'http://ddex.net/xml/avs/avs',
        'ds': 'http://www.w3.org/2000/09/xmldsig#'
    }
    root = etree.Element(
        '{http://ddex.net/xml/ern-c-sftp/16}ManifestMessage',
        nsmap=new_nsmap,
        attrib={
            'MessageVersionId': 'ern-c-sftp/16',
            '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation': 'http://ddex.net/xml/ern-c-sftp/16 http://ddex.net/xml/ern-c-sftp/16/ern-choreography-sftp.xsd'
        }
    )
    
    message_header = etree.SubElement(root, 'MessageHeader')
    message_sender = etree.SubElement(message_header, 'MessageSender')
    party_id = etree.SubElement(message_sender, 'PartyId')
    party_id.text = 'PADPIDA2021092801S'
    party_name = etree.SubElement(message_sender, 'PartyName')
    full_name = etree.SubElement(party_name, 'FullName')
    full_name.text = 'BeatData.Pro, LLC'
    
    message_recipient = etree.SubElement(message_header, 'MessageRecipient')
    party_id = etree.SubElement(message_recipient, 'PartyId')
    party_id.text = 'PADPIDA2021092801S'
    party_name = etree.SubElement(message_recipient, 'PartyName')
    full_name = etree.SubElement(party_name, 'FullName')
    full_name.text = 'BeatData.Pro, LLC'
    
    message_created_date_time = etree.SubElement(message_header, 'MessageCreatedDateTime')
    message_created_date_time.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    
    is_test_flag = etree.SubElement(root, 'IsTestFlag')
    is_test_flag.text = 'false'
    
    root_directory = etree.SubElement(root, 'RootDirectory')
    root_directory.text = './'
    
    number_of_messages = etree.SubElement(root, 'NumberOfMessages')
    number_of_messages.text = str(len(package_folders))
    
    for i in range(len(package_folders)):
        message_in_batch = etree.SubElement(root, 'MessageInBatch')
        message_type = etree.SubElement(message_in_batch, 'MessageType')
        message_type.text = 'NewReleaseMessage'
        
        message_id_element = etree.SubElement(message_in_batch, 'MessageId')
        message_id_element.text = message_ids[i]
        
        url = etree.SubElement(message_in_batch, 'URL')
        url.text = f'./{package_folders[i]}/{xml_file_names[i]}'
        
        included_release_id = etree.SubElement(message_in_batch, 'IncludedReleaseId')
        icpn_element = etree.SubElement(included_release_id, 'ICPN')
        icpn_element.text = icpns[i]
        
        delivery_type = etree.SubElement(message_in_batch, 'DeliveryType')
        delivery_type.text = 'NewReleaseDelivery'
        
        product_type = etree.SubElement(message_in_batch, 'ProductType')
        product_type.text = 'AudioProduct'
        
        hash_sum_element = etree.SubElement(message_in_batch, 'HashSum')
        hash_sum_value = etree.SubElement(hash_sum_element, 'HashSum')
        hash_sum_value.text = hash_sums[i]
        hash_sum_algorithm_type = etree.SubElement(hash_sum_element, 'HashSumAlgorithmType')
        hash_sum_algorithm_type.text = 'MD5'
    
    new_tree = etree.ElementTree(root)
    new_tree.write(batch_complete_path, encoding='utf-8', xml_declaration=True, pretty_print=True)

def main():
    input_folder = './INPUT'  # Default input folder path
    output_folder = './OUTPUT'  # Default output folder path

    for batch_folder in os.listdir(input_folder):
        batch_folder_path = os.path.join(input_folder, batch_folder)
        if os.path.isdir(batch_folder_path):
            package_folders = []
            xml_file_names = []
            message_ids = []
            icpns = []
            hash_sums = []
            
            for package_folder in os.listdir(batch_folder_path):
                package_folder_path = os.path.join(batch_folder_path, package_folder)
                if os.path.isdir(package_folder_path):
                    input_xml_path = os.path.join(package_folder_path, f"{package_folder}.xml")
                    print(f"Processing XML file: {input_xml_path}")
                    if os.path.exists(input_xml_path):
                        resources_folder = os.path.join(package_folder_path, 'resources')
                        if not os.path.exists(resources_folder):
                            print(f"Error: The resources folder {resources_folder} does not exist. Skipping this package.")
                            continue

                        output_xml_path = os.path.join(output_folder, batch_folder, package_folder, f"{package_folder}.xml")
                        output_folder_path = os.path.dirname(output_xml_path)
                        if os.path.exists(output_folder_path):
                            shutil.rmtree(output_folder_path)
                        os.makedirs(output_folder_path, exist_ok=True)

                        output_xml_path = convert_ddex_structure(input_xml_path, output_xml_path, resources_folder, package_folder)
                        if output_xml_path is None:
                            continue
                        
                        dst_resources = os.path.join(output_folder, batch_folder, package_folder, 'resources')
                        print(f"Copying resources from {resources_folder} to {dst_resources}")
                        copy_resources(resources_folder, dst_resources)
                        
                        hash_sum = calculate_md5(output_xml_path)
                        
                        message_id = package_folder
                        icpn = package_folder
                        xml_file_name = f"{package_folder}.xml"
                        
                        package_folders.append(package_folder)
                        xml_file_names.append(xml_file_name)
                        message_ids.append(message_id)
                        icpns.append(icpn)
                        hash_sums.append(hash_sum)
                    else:
                        print(f"Error: The XML file {input_xml_path} does not exist.")
            
            if package_folders:
                create_batch_complete_xml(output_folder, batch_folder, package_folders, xml_file_names, message_ids, icpns, hash_sums)

if __name__ == '__main__':
    main()