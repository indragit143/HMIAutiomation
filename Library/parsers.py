

from xml.dom import minidom
import time



class LangStringParser():
    def __init__(self, lang_str_filepath):
        self.doc = minidom.parse(lang_str_filepath)
        
    def get_string_table_with_id(self, lang):
        items_tags = self.doc.getElementsByTagName("Item")
        string_table = {}        
        for items_tag in items_tags: 
            sid = items_tag.getAttribute("Id")           
            try:                
                lang_ele = items_tag.getElementsByTagName(lang)[0]
                items_tag.childNodes
                nodelist = lang_ele.childNodes
                string_value = nodelist[-1].data
                string_table[sid] = string_value
            except:
                string_table[sid] = ""
        return string_table        
        
    def get_string_table_of_all_lang(self):
        languages = ['en-GB', 'de-DE', 'fr-FR', 'es-ES', 'it-IT', 'pt-PT', 'ru-RU', 'nl-NL', 'bg-BG', 'cs-CZ', 'et-EE',
                     'fi-FI', 'el-GR', 'hu-HU', 'lt-LT', 'no-NL', 'pl-PL', 'sv-SE', 'tr-TR', 'sr LB', 'lv-LT', 'ro-RO',
                     'sk-SK', 'sl-SI', 'hr-HR', 'zh-CN', 'ko-KR']
        all_lang_string_table = {}
        for language in languages:
            each_lang_string_table = self.get_string_table_with_id(language)
            all_lang_string_table[language] = each_lang_string_table
        return all_lang_string_table
    
    def get_strings_with_english(self, lang):
        eng_local_strings = {}
        eng_strings = self.get_string_table_with_id('en-GB')
        
        local_strings = self.get_string_table_with_id(lang)
        
        for string_id in eng_strings:
            eng_local_strings[eng_strings[string_id]] = local_strings[string_id]
            
        return eng_local_strings
            
        
        