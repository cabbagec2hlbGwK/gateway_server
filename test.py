import re

def swap_dict(input_dict):
    output_dict = {}
    for key, values in input_dict.items():
        for value in values:
            output_dict[value] = key
    return output_dict

def cardCheck(card_number: str) -> bool:
    card_number = card_number.replace(" ", "")
    reversed_digits = [int(d) for d in card_number[::-1]]
    
    total = 0
    for i, digit in enumerate(reversed_digits):
        if i % 2 == 1:  
            doubled = digit * 2
            if doubled > 9:  
                total += (doubled - 9)  
            else:
                total += doubled
        else:
            total += digit
    return total % 10 == 0

def extractNumbers(text, num_chars):
    cleaned_text = re.sub(r'[^0-9]', '', text)
    results = []
    for i in range(len(cleaned_text) - num_chars + 1):
        results.append(cleaned_text[i:i + num_chars])
    
    return results
def extract_card_info(text):
    card_patterns = {
        14: {
            'Diners Club Carte Blanche': r'^(300|301|302|303|304|305)[0-9]{11}$',
            'Diners Club International': r'^36[0-9]{12}$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
            'Visa': r'^4[0-9]{14}$',
        },
        15: {
            'American Express': r'^(34|37)[0-9]{13}$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
        },
        16: {
            'Diners Club US and Canada': r'^(54|55)[0-9]{14}$',
            'Discover Card': r'^(6011|622[1-9][0-9]{5}|64[4-9][0-9]{13}|65[0-9]{14})[0-9]{12}$',
            'InstaPayment': r'^(637|638|639)[0-9]{13}$',
            'JCB': r'^(352[8-9]|35[3-8][0-9])[0-9]{12}$',
            'Mastercard': r'^(5[1-5][0-9]{14}|2221[0-9]{12}|22[2-7][0-9]{13}|2720[0-9]{12})$',
            'Visa': r'^4[0-9]{15}$',
            'Visa Electron': r'^(4026[0-9]{12}|417500[0-9]{10}|4508[0-9]{12}|4844[0-9]{12}|4913[0-9]{12}|4917[0-9]{12})$',
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
        },
        19: {
            'Maestro': r'^(5018|5020|5038|5893|6304|6759|6761|6762|6763)[0-9]{12,15}$',
            'Visa': r'^4[0-9]{18}$',
            'Discover Card': r'^(6011[0-9]{15}|622[12][0-9]{13}|622[3-8][0-9]{14}|6229[0-2][0-9]{13}|644[0-9]{15}|645[0-9]{15}|646[0-9]{15}|647[0-9]{15}|648[0-9]{15}|649[0-9]{15}|65[0-9]{17})$',
            'Laser': r'^(6304|6706|6771|6709)[0-9]{15,18}$', 
            'JCB': r'^(352[8-9]|35[3-8][0-9])[0-9]{12,15}$',
        },
    }

    matches = dict()

    for key, patterns in card_patterns.items():
        data = extractNumbers(text, key)
        print(len(data))
        if data == []:
            pass
            return matches
        for card_number in data:
            for name, pattern in patterns.items():
                if re.fullmatch(pattern, card_number) and cardCheck(card_number):
                    mat = matches.get(name, list())
                    mat.append(card_number)
                    matches[name] = mat
    return matches




text = """
 VISA
4556829130518329
4716725048227804
4716694490334070100
MasterCard
5526807662668229
5211020149292916
2720993606527332
American Express (AMEX)
373695022117036
379142214470018
340962237994595
Discover
6011402482581602
6011445788020924
6011850272321948751
JCB
3532972460923098
3528072410849422
3544270883087389496
Diners Club - North America
5454734996831495
5539359484649727
Diners Club - Carte Blanche
30075949882613
30509121302974
30494731422258
Diners Club - International
36882471317171
36402099400679
36679834402918
Maestro
6761333084198465
6762273117591337
5018737722505225
Visa Electron
4026393805157162
4917517349582038
4175002410422718
InstaPayment
6374901461594982
6387321817010820
6392341432593284
"""
results = extract_card_info(text)
print(swap_dict(results))

