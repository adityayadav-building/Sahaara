"""Built-in starter corpus so the app works before any books are ingested.

* Sanskrit verses are public domain. Transliterations (IAST) are included for reading aloud.
  >>> Verify every verse against a trusted edition (e.g. Gita Supersite / Gita Press) before you
  >>> ship: this file was typed by hand.
* The English/Hindi "meaning" lines are original plain-language paraphrases written for this
  project, NOT copied from any published translation.
* Practices, thinking tools and story summaries are original wording of widely known, general
  techniques and folk tales (Panchatantra). They are not medical advice.

Add your own books with backend/scripts/ingest.py; they load from data/corpus/user/*.jsonl.
"""
from __future__ import annotations

SOURCE_GITA = "Bhagavad Gita"

SHLOKAS = [
    dict(
        id="gita-2-47", ref="2.47",
        topics=["anxiety", "exam_pressure", "failure", "overwhelm", "low_motivation"],
        sanskrit="कर्मण्येवाधिकारस्ते मा फलेषु कदाचन ।\nमा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥",
        iast="karmaṇy evādhikāras te mā phaleṣu kadācana |\nmā karma-phala-hetur bhūr mā te saṅgo 'stv akarmaṇi ||",
        meaning_en="Your right is to the action alone, never to its fruits. Do not make the reward your reason for acting, and do not slip into doing nothing either.",
        meaning_hi="आपका अधिकार केवल कर्म करने पर है, उसके फल पर नहीं। फल को अपना कारण मत बनाइए, और काम छोड़कर बैठ भी मत जाइए।",
        keywords=["result", "phal", "fruit", "effort", "mehnat", "outcome", "नतीजा", "फल", "मेहनत", "result ki chinta"],
    ),
    dict(
        id="gita-2-14", ref="2.14",
        topics=["sadness", "grief", "anxiety", "burnout"],
        sanskrit="मात्रास्पर्शास्तु कौन्तेय शीतोष्णसुखदुःखदाः ।\nआगमापायिनोऽनित्यास्तांस्तितिक्षस्व भारत ॥",
        iast="mātrā-sparśās tu kaunteya śītoṣṇa-sukha-duḥkha-dāḥ |\nāgamāpāyino 'nityās tāṁs titikṣasva bhārata ||",
        meaning_en="Experiences bring heat and cold, pleasure and pain. They come and they go and none of them stay, so learn to bear them with patience.",
        meaning_hi="अनुभवों से सर्दी-गर्मी, सुख-दुख आते हैं। वे आते-जाते रहते हैं, टिकते नहीं, इसलिए उन्हें धैर्य से सहना सीखिए।",
        keywords=["temporary", "pain", "passes", "bad phase", "bura waqt", "waqt guzar", "यह भी गुज़र", "अस्थायी", "बुरा वक्त"],
    ),
    dict(
        id="gita-2-48", ref="2.48",
        topics=["failure", "exam_pressure", "anxiety", "low_motivation"],
        sanskrit="योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय ।\nसिद्ध्यसिद्ध्योः समो भूत्वा समत्वं योग उच्यते ॥",
        iast="yoga-sthaḥ kuru karmāṇi saṅgaṁ tyaktvā dhanañjaya |\nsiddhy-asiddhyoḥ samo bhūtvā samatvaṁ yoga ucyate ||",
        meaning_en="Stay steady and do your work, letting go of clinging. Be the same in success and in failure. This evenness of mind is what is called yoga.",
        meaning_hi="जुड़ाव छोड़कर, स्थिर मन से अपना काम कीजिए। सफलता और असफलता में एक-सा रहना ही योग कहलाता है।",
        keywords=["success", "failure", "balance", "equanimity", "safalta", "asafalta", "सफलता", "असफलता", "संतुलन"],
    ),
    dict(
        id="gita-6-5", ref="6.5",
        topics=["self_worth", "low_motivation", "guilt", "failure"],
        sanskrit="उद्धरेदात्मनात्मानं नात्मानमवसादयेत् ।\nआत्मैव ह्यात्मनो बन्धुरात्मैव रिपुरात्मनः ॥",
        iast="uddhared ātmanātmānaṁ nātmānam avasādayet |\nātmaiva hy ātmano bandhur ātmaiva ripur ātmanaḥ ||",
        meaning_en="Lift yourself up with your own mind and do not pull yourself down. You can be your own best friend, or your own worst enemy.",
        meaning_hi="अपने मन से खुद को ऊपर उठाइए, खुद को गिराइए मत। आप खुद अपने मित्र हो सकते हैं और खुद अपने शत्रु भी।",
        keywords=["self", "khud", "self criticism", "own friend", "apna dost", "खुद", "अपना दोस्त", "आत्म"],
    ),
    dict(
        id="gita-6-35", ref="6.35",
        topics=["overthinking", "anxiety", "low_motivation"],
        sanskrit="असंशयं महाबाहो मनो दुर्निग्रहं चलम् ।\nअभ्यासेन तु कौन्तेय वैराग्येण च गृह्यते ॥",
        iast="asaṁśayaṁ mahā-bāho mano durnigrahaṁ calam |\nabhyāsena tu kaunteya vairāgyeṇa ca gṛhyate ||",
        meaning_en="There is no doubt the mind is restless and hard to hold. But with steady practice, and by loosening its grip on things, it can be trained.",
        meaning_hi="इसमें संदेह नहीं कि मन चंचल है और इसे काबू में करना कठिन है। पर लगातार अभ्यास से और पकड़ ढीली करने से यह वश में आता है।",
        keywords=["restless", "mind", "focus", "meditation", "practice", "abhyas", "mann", "chanchal", "मन", "अभ्यास", "ध्यान", "चंचल"],
    ),
    dict(
        id="gita-2-62-63", ref="2.62–63",
        topics=["anger", "relationships"],
        sanskrit="ध्यायतो विषयान्पुंसः सङ्गस्तेषूपजायते ।\nसङ्गात्सञ्जायते कामः कामात्क्रोधोऽभिजायते ॥\nक्रोधाद्भवति सम्मोहः सम्मोहात्स्मृतिविभ्रमः ।\nस्मृतिभ्रंशाद्बुद्धिनाशो बुद्धिनाशात्प्रणश्यति ॥",
        iast="dhyāyato viṣayān puṁsaḥ saṅgas teṣūpajāyate |\nsaṅgāt sañjāyate kāmaḥ kāmāt krodho 'bhijāyate ||\nkrodhād bhavati sammohaḥ sammohāt smṛti-vibhramaḥ |\nsmṛti-bhraṁśād buddhi-nāśo buddhi-nāśāt praṇaśyati ||",
        meaning_en="Dwelling on something builds attachment to it, attachment builds desire, and when desire is blocked, anger is born. Anger clouds the mind, the mind loses its clarity, and a person can fall apart.",
        meaning_hi="किसी बात को बार-बार सोचने से उससे लगाव होता है, लगाव से इच्छा, और इच्छा रुकने पर क्रोध पैदा होता है। क्रोध से मन पर धुंध छा जाती है, समझ खो जाती है, और इंसान टूट सकता है।",
        keywords=["anger", "gussa", "krodh", "rage", "temper", "irritated", "गुस्सा", "क्रोध", "चिढ़"],
        note="Chain of anger: dwelling, attachment, desire, anger, confusion. Useful for showing where to pause.",
    ),
    dict(
        id="gita-6-17", ref="6.17",
        topics=["sleep", "burnout", "overwhelm", "anxiety"],
        sanskrit="युक्ताहारविहारस्य युक्तचेष्टस्य कर्मसु ।\nयुक्तस्वप्नावबोधस्य योगो भवति दुःखहा ॥",
        iast="yuktāhāra-vihārasya yukta-ceṣṭasya karmasu |\nyukta-svapnāvabodhasya yogo bhavati duḥkha-hā ||",
        meaning_en="For one who is balanced in eating and rest, in effort, and in sleeping and waking, yoga becomes the remover of sorrow.",
        meaning_hi="जिसका खाना-पीना, आराम, काम और सोना-जागना संतुलित है, उसके लिए योग दुखों को दूर करने वाला बन जाता है।",
        keywords=["routine", "sleep", "balance", "food", "rest", "neend", "dincharya", "नींद", "दिनचर्या", "संतुलन", "आराम"],
    ),
    dict(
        id="gita-2-22", ref="2.22",
        topics=["grief", "sadness"],
        sanskrit="वासांसि जीर्णानि यथा विहाय नवानि गृह्णाति नरोऽपराणि ।\nतथा शरीराणि विहाय जीर्णान्यन्यानि संयाति नवानि देही ॥",
        iast="vāsāṁsi jīrṇāni yathā vihāya navāni gṛhṇāti naro 'parāṇi |\ntathā śarīrāṇi vihāya jīrṇāny anyāni saṁyāti navāni dehī ||",
        meaning_en="As a person sets aside worn-out clothes and puts on new ones, the one who lives within sets aside worn-out bodies and takes on new ones.",
        meaning_hi="जैसे इंसान पुराने कपड़े उतारकर नए पहन लेता है, वैसे ही शरीर में रहने वाला पुराने शरीर छोड़कर नए धारण करता है।",
        keywords=["death", "loss", "passed away", "mrityu", "nidhan", "मृत्यु", "निधन", "शोक"],
        note="Use very gently and only after listening. Never rush a grieving person to 'accept' loss; let the verse be an offering, not an argument.",
    ),
    dict(
        id="gita-2-38", ref="2.38",
        topics=["failure", "exam_pressure", "anxiety"],
        sanskrit="सुखदुःखे समे कृत्वा लाभालाभौ जयाजयौ ।\nततो युद्धाय युज्यस्व नैवं पापमवाप्स्यसि ॥",
        iast="sukha-duḥkhe same kṛtvā lābhālābhau jayājayau |\ntato yuddhāya yujyasva naivaṁ pāpam avāpsyasi ||",
        meaning_en="Hold pleasure and pain, gain and loss, victory and defeat as the same, and then take up your task. Acting this way, you carry no blame.",
        meaning_hi="सुख-दुख, लाभ-हानि और जीत-हार को समान मानकर अपने कर्तव्य में लगिए। ऐसे करने पर आप दोष के भागी नहीं बनते।",
        keywords=["win", "lose", "setback", "jeet", "haar", "labh", "हार", "जीत", "लाभ", "हानि"],
    ),
    dict(
        id="gita-12-13", ref="12.13",
        topics=["relationships", "anger", "guilt", "self_worth"],
        sanskrit="अद्वेष्टा सर्वभूतानां मैत्रः करुण एव च ।\nनिर्ममो निरहङ्कारः समदुःखसुखः क्षमी ॥",
        iast="adveṣṭā sarva-bhūtānāṁ maitraḥ karuṇa eva ca |\nnirmamo nirahaṅkāraḥ sama-duḥkha-sukhaḥ kṣamī ||",
        meaning_en="Dear is the one who holds no hatred for any being, who is friendly and compassionate, free from possessiveness and ego, steady in pain and pleasure, and forgiving.",
        meaning_hi="प्रिय वह है जो किसी से द्वेष नहीं रखता, जो मित्रवत और करुणावान है, जिसमें 'मेरा-मेरा' और अहंकार नहीं है, जो सुख-दुख में एक-सा रहता है और क्षमा करना जानता है।",
        keywords=["forgive", "forgiveness", "kshama", "maaf", "resentment", "compassion", "karuna", "माफ", "क्षमा", "करुणा", "नफ़रत"],
    ),
    dict(
        id="gita-2-56", ref="2.56",
        topics=["sadness", "anxiety", "fear", "anger"],
        sanskrit="दुःखेष्वनुद्विग्नमनाः सुखेषु विगतस्पृहः ।\nवीतरागभयक्रोधः स्थितधीर्मुनिरुच्यते ॥",
        iast="duḥkheṣv anudvigna-manāḥ sukheṣu vigata-spṛhaḥ |\nvīta-rāga-bhaya-krodhaḥ sthita-dhīr munir ucyate ||",
        meaning_en="One whose mind is not shaken by sorrow, who does not crave pleasure, and who is free from clinging, fear and anger is called steady in wisdom.",
        meaning_hi="जिसका मन दुखों में डगमगाता नहीं, जो सुखों की लालसा नहीं रखता और जो लगाव, भय व क्रोध से मुक्त है, वह स्थिर बुद्धि वाला कहलाता है।",
        keywords=["steady", "calm", "stable", "sthir", "shant", "स्थिर", "शांत", "धैर्य"],
    ),
    dict(
        id="gita-18-66", ref="18.66",
        topics=["overwhelm", "guilt", "burnout", "fear", "sadness"],
        sanskrit="सर्वधर्मान्परित्यज्य मामेकं शरणं व्रज ।\nअहं त्वां सर्वपापेभ्यो मोक्षयिष्यामि मा शुचः ॥",
        iast="sarva-dharmān parityajya mām ekaṁ śaraṇaṁ vraja |\nahaṁ tvāṁ sarva-pāpebhyo mokṣayiṣyāmi mā śucaḥ ||",
        meaning_en="Put down all the heavy duties you are clutching and come to Me alone for refuge. I will free you from every burden; do not grieve.",
        meaning_hi="सारे भारी कर्तव्यों और चिंताओं को छोड़कर मेरी शरण में आ जाइए। मैं आपको हर बोझ से मुक्त कर दूँगा, शोक मत कीजिए।",
        keywords=["surrender", "burden", "let go", "refuge", "sharan", "bojh", "शरण", "बोझ", "छोड़ दो"],
        note="Faith-based: offer as comfort for people who respond to devotion; otherwise lean on the idea of setting a burden down.",
    ),
    dict(
        id="gita-9-22", ref="9.22",
        topics=["loneliness", "fear", "sadness", "overwhelm"],
        sanskrit="अनन्याश्चिन्तयन्तो मां ये जनाः पर्युपासते ।\nतेषां नित्याभियुक्तानां योगक्षेमं वहाम्यहम् ॥",
        iast="ananyāś cintayanto māṁ ye janāḥ paryupāsate |\nteṣāṁ nityābhiyuktānāṁ yoga-kṣemaṁ vahāmy aham ||",
        meaning_en="For those who keep Me in mind with a steady heart, I carry what they lack and protect what they have.",
        meaning_hi="जो लोग एकनिष्ठ भाव से मुझे याद करते हैं, उनकी ज़रूरतों का और जो उनके पास है उसकी रक्षा का भार मैं उठाता हूँ।",
        keywords=["alone", "support", "faith", "trust", "sahara", "bharosa", "akela", "सहारा", "भरोसा", "विश्वास", "अकेला"],
        note="Faith-based comfort: 'you are not carrying everything alone'. Pair with a human reach-out step.",
    ),
    dict(
        id="gita-2-40", ref="2.40",
        topics=["fear", "low_motivation", "anxiety", "overwhelm"],
        sanskrit="नेहाभिक्रमनाशोऽस्ति प्रत्यवायो न विद्यते ।\nस्वल्पमप्यस्य धर्मस्य त्रायते महतो भयात् ॥",
        iast="nehābhikrama-nāśo 'sti pratyavāyo na vidyate |\nsvalpam apy asya dharmasya trāyate mahato bhayāt ||",
        meaning_en="On this path no effort is wasted and starting does no harm. Even a little of this practice protects you from great fear.",
        meaning_hi="इस मार्ग में किया गया प्रयास व्यर्थ नहीं जाता और शुरू करने में कोई हानि नहीं है। थोड़ा-सा अभ्यास भी बड़े भय से बचाता है।",
        keywords=["start small", "little", "begin", "fear", "shuruaat", "thoda", "डर", "शुरुआत", "थोड़ा"],
    ),
]

PRACTICES = [
    dict(
        id="practice-long-exhale", title_en="Long-exhale breathing", title_hi="लंबी साँस छोड़ने का अभ्यास",
        topics=["anxiety", "fear", "overwhelm", "exam_pressure", "general"], breath="long_exhale", minutes=2,
        steps_en=[
            "Sit comfortably and let your shoulders drop.",
            "Breathe in slowly through your nose, counting to four.",
            "Breathe out gently through your mouth, counting to six, as if cooling hot tea.",
            "Repeat for two minutes. If you feel dizzy, go back to normal breathing.",
        ],
        steps_hi=[
            "आराम से बैठिए और कंधे ढीले छोड़ दीजिए।",
            "नाक से धीरे-धीरे साँस अंदर लीजिए, चार तक गिनिए।",
            "मुँह से हल्के-हल्के साँस बाहर छोड़िए, छह तक गिनिए, जैसे गरम चाय को ठंडा कर रहे हों।",
            "दो मिनट दोहराइए। चक्कर जैसा लगे तो सामान्य साँस पर लौट आइए।",
        ],
        keywords=["breathing", "pranayama", "calm down", "panic", "saans", "साँस", "सांस", "प्राणायाम"],
    ),
    dict(
        id="practice-box", title_en="Box breathing", title_hi="चौकोर साँस (बॉक्स ब्रीदिंग)",
        topics=["anxiety", "overthinking", "exam_pressure", "fear"], breath="box", minutes=3,
        steps_en=[
            "Breathe in for four counts.",
            "Hold gently for four counts.",
            "Breathe out for four counts.",
            "Rest for four counts, then repeat. If holding the breath feels uncomfortable, simply skip the holds.",
        ],
        steps_hi=[
            "चार गिनती तक साँस अंदर लीजिए।",
            "चार गिनती तक हल्के से रोकिए।",
            "चार गिनती तक साँस बाहर छोड़िए।",
            "चार गिनती रुकिए, फिर दोहराइए। साँस रोकना असहज लगे तो रोकना छोड़ दीजिए।",
        ],
        keywords=["focus", "exam", "calm", "breathing", "ब्रीदिंग"],
    ),
    dict(
        id="practice-nadi", title_en="Alternate-nostril breathing (gentle)", title_hi="नाड़ी शोधन (हल्का अभ्यास)",
        topics=["overthinking", "anxiety", "sleep", "burnout"], breath="nadi", minutes=4,
        steps_en=[
            "Sit with a straight, relaxed back. Rest your left hand on your knee.",
            "Close your right nostril with your thumb and breathe in slowly through the left.",
            "Close the left nostril with your ring finger, open the right, and breathe out slowly.",
            "Breathe in through the right, switch, and breathe out through the left. That is one round; do five. No breath-holding. Stop if you feel dizzy or your nose is blocked.",
        ],
        steps_hi=[
            "पीठ सीधी और शरीर ढीला रखकर बैठिए। बायाँ हाथ घुटने पर रखिए।",
            "दाएँ अँगूठे से दाहिना नथुना बंद कीजिए और बाएँ से धीरे-धीरे साँस लीजिए।",
            "अनामिका उँगली से बायाँ नथुना बंद कीजिए, दायाँ खोलिए और धीरे-धीरे साँस छोड़िए।",
            "दाएँ से साँस लीजिए, बदलिए और बाएँ से छोड़िए। यह एक चक्र है; पाँच चक्र कीजिए। साँस रोकिए नहीं। चक्कर आए या नाक बंद हो तो रुक जाइए।",
        ],
        keywords=["nadi shodhana", "anulom vilom", "alternate nostril", "अनुलोम विलोम", "नाड़ी शोधन"],
    ),
    dict(
        id="practice-bhramari", title_en="Humming-bee breath (Bhramari)", title_hi="भ्रामरी (भौंरे जैसी गुंजन)",
        topics=["anger", "overthinking", "sadness", "sleep", "anxiety"], breath="bhramari", minutes=2,
        steps_en=[
            "Sit comfortably and close your eyes.",
            "Breathe in slowly through the nose.",
            "As you breathe out, make a soft humming sound like a bee, and feel the buzz in your head and chest.",
            "Repeat five to seven times, then sit quietly for a few breaths.",
        ],
        steps_hi=[
            "आराम से बैठिए और आँखें बंद कर लीजिए।",
            "नाक से धीरे-धीरे साँस अंदर लीजिए।",
            "साँस छोड़ते समय भौंरे की तरह हल्की गुनगुनाहट कीजिए और सिर व सीने में कंपन महसूस कीजिए।",
            "पाँच से सात बार दोहराइए, फिर कुछ साँसें चुपचाप बैठे रहिए।",
        ],
        keywords=["humming", "bee", "bhramari", "भ्रामरी", "गुंजन"],
    ),
    dict(
        id="practice-grounding", title_en="5-4-3-2-1 grounding", title_hi="५-४-३-२-१ ग्राउंडिंग",
        topics=["anxiety", "fear", "overwhelm", "overthinking"], breath=None, minutes=3,
        steps_en=[
            "Look around and name five things you can see.",
            "Name four things you can touch, and touch them.",
            "Name three sounds you can hear.",
            "Name two things you can smell, and one thing you can taste. Take a slow breath.",
        ],
        steps_hi=[
            "चारों ओर देखिए और पाँच चीज़ें गिनाइए जो आपको दिख रही हैं।",
            "चार चीज़ें बताइए जिन्हें आप छू सकते हैं, और उन्हें छूकर देखिए।",
            "तीन आवाज़ें बताइए जो आपको सुनाई दे रही हैं।",
            "दो चीज़ें जिनकी खुशबू आ रही है और एक स्वाद बताइए। फिर एक धीमी साँस लीजिए।",
        ],
        keywords=["panic", "grounding", "present moment", "ghabrahat", "घबराहट"],
    ),
    dict(
        id="practice-body-scan", title_en="Slow body relaxation", title_hi="शरीर को ढीला करने का अभ्यास",
        topics=["sleep", "anxiety", "burnout", "anger"], breath=None, minutes=5,
        steps_en=[
            "Lie down or sit back and close your eyes.",
            "Tighten your feet for five seconds, then let them go soft.",
            "Move upward: legs, belly, hands, shoulders, face, tightening then releasing each part.",
            "Finish with three slow breaths and notice how your body feels now.",
        ],
        steps_hi=[
            "लेट जाइए या पीछे टिककर आँखें बंद कर लीजिए।",
            "पाँच सेकंड के लिए पैरों को कस लीजिए, फिर उन्हें ढीला छोड़ दीजिए।",
            "ऊपर बढ़ते जाइए: टाँगें, पेट, हाथ, कंधे, चेहरा। हर हिस्से को कसिए और फिर ढीला कीजिए।",
            "तीन धीमी साँसों के साथ खत्म कीजिए और महसूस कीजिए कि अब शरीर कैसा लग रहा है।",
        ],
        keywords=["relax", "tension in body", "muscle", "neend", "नींद", "आराम"],
    ),
    dict(
        id="practice-sleep", title_en="Wind-down for sleep", title_hi="नींद से पहले का सुकून",
        topics=["sleep", "overthinking", "anxiety"], breath=None, minutes=15,
        steps_en=[
            "Keep a fixed bedtime and put your phone away from the bed about thirty minutes before.",
            "Write down tomorrow's worries on paper so your mind does not have to hold them overnight.",
            "Wash your face and feet with cool water, and dim the lights.",
            "In bed, breathe out for longer than you breathe in until you feel drowsy.",
        ],
        steps_hi=[
            "सोने का समय तय रखिए और लगभग तीस मिनट पहले फ़ोन बिस्तर से दूर रख दीजिए।",
            "कल की चिंताएँ कागज़ पर लिख दीजिए ताकि मन को उन्हें रात भर पकड़कर न रखना पड़े।",
            "ठंडे पानी से मुँह-पैर धोइए और रोशनी धीमी कर दीजिए।",
            "बिस्तर पर साँस अंदर से ज़्यादा देर तक बाहर छोड़िए, जब तक नींद न आने लगे।",
        ],
        keywords=["insomnia", "bedtime", "night", "raat", "neend", "रात", "नींद"],
    ),
    dict(
        id="practice-diya", title_en="Diya reflection: three small lights", title_hi="दीया चिंतन: तीन छोटी रोशनियाँ",
        topics=["sadness", "grief", "loneliness", "general"], breath=None, minutes=3,
        steps_en=[
            "If you can, light a small diya, or simply imagine one steady flame.",
            "Think of three small good things from today, even tiny ones like warm tea or a kind word.",
            "Say them aloud or write them down, one for each light.",
            "Watch the flame for a few breaths and let the day soften.",
        ],
        steps_hi=[
            "हो सके तो एक छोटा दीया जलाइए, या बस एक स्थिर लौ की कल्पना कीजिए।",
            "आज की तीन छोटी अच्छी बातें सोचिए, चाहे बहुत छोटी हों, जैसे गरम चाय या किसी की मीठी बात।",
            "हर रोशनी के लिए एक बात ज़ोर से बोलिए या लिख लीजिए।",
            "कुछ साँसों तक लौ को देखिए और दिन को नरम होने दीजिए।",
        ],
        keywords=["gratitude", "diya", "light", "hope", "dhanyavad", "दीया", "आभार", "उम्मीद"],
    ),
    dict(
        id="practice-walk", title_en="Ten-minute walk", title_hi="दस मिनट की सैर",
        topics=["low_motivation", "sadness", "burnout", "overthinking", "anger"], breath=None, minutes=10,
        steps_en=[
            "Put on your shoes and step outside, even if you only walk around the block.",
            "Walk at an easy pace for ten minutes.",
            "Notice your feet touching the ground and the sky above you.",
            "Come back and drink a glass of water.",
        ],
        steps_hi=[
            "जूते पहनिए और बाहर निकल जाइए, चाहे सिर्फ़ गली का एक चक्कर ही लगाएँ।",
            "दस मिनट आराम की चाल से चलिए।",
            "ध्यान दीजिए कि पैर ज़मीन को कैसे छू रहे हैं और ऊपर आसमान कैसा है।",
            "लौटकर एक गिलास पानी पीजिए।",
        ],
        keywords=["walk", "exercise", "move", "tahalna", "sair", "सैर", "टहलना"],
    ),
    dict(
        id="practice-anger-pause", title_en="The ten-breath pause", title_hi="दस साँसों का ठहराव",
        topics=["anger", "relationships"], breath="long_exhale", minutes=2,
        steps_en=[
            "When anger rises, do not answer yet. Step away if you can.",
            "Take ten slow breaths, breathing out longer than you breathe in.",
            "Splash cool water on your face or hands.",
            "Only then decide whether to speak, and what is truly worth saying.",
        ],
        steps_hi=[
            "जब गुस्सा चढ़े, तुरंत जवाब मत दीजिए। हो सके तो वहाँ से हट जाइए।",
            "दस धीमी साँसें लीजिए, छोड़ते समय साँस लेने से ज़्यादा देर लगाइए।",
            "चेहरे या हाथों पर ठंडा पानी डालिए।",
            "इसके बाद तय कीजिए कि बोलना है या नहीं, और क्या कहना सचमुच ज़रूरी है।",
        ],
        keywords=["cool down", "calm", "temper", "gussa", "गुस्सा", "ठहराव"],
    ),
    dict(
        id="practice-journal", title_en="Five-minute worry page", title_hi="पाँच मिनट का चिंता-पन्ना",
        topics=["overthinking", "guilt", "anxiety", "relationships", "overwhelm"], breath=None, minutes=5,
        steps_en=[
            "Take a page and set a timer for five minutes.",
            "Write everything on your mind without fixing it.",
            "Draw a line down the page. On one side list what you can control, on the other what you cannot.",
            "Pick one small thing from the first side to do today.",
        ],
        steps_hi=[
            "एक पन्ना लीजिए और पाँच मिनट का टाइमर लगाइए।",
            "जो भी मन में है बिना सुधारे लिख डालिए।",
            "पन्ने के बीच में एक रेखा खींचिए। एक तरफ़ वह लिखिए जो आपके हाथ में है, दूसरी तरफ़ वह जो नहीं है।",
            "पहली तरफ़ से एक छोटी-सी चीज़ चुनिए जो आज कर सकें।",
        ],
        keywords=["write", "journal", "diary", "likhna", "डायरी", "लिखना"],
    ),
    dict(
        id="practice-reach-out", title_en="Reach out to one person", title_hi="एक इंसान तक पहुँचिए",
        topics=["loneliness", "sadness", "self_worth", "grief", "overwhelm"], breath=None, minutes=5,
        steps_en=[
            "Think of one person who has been kind to you, even once.",
            "Send a short message: 'Thinking of you. Can we talk for a few minutes today?'",
            "If talking feels too hard, ask to simply sit together or walk together.",
            "Speaking to a person is a strength, not a burden on them.",
        ],
        steps_hi=[
            "किसी एक ऐसे इंसान के बारे में सोचिए जो कभी भी आपके साथ अच्छा रहा हो।",
            "एक छोटा संदेश भेजिए: 'आपकी याद आ रही थी। क्या आज कुछ देर बात कर सकते हैं?'",
            "अगर बात करना मुश्किल लगे, तो बस साथ बैठने या साथ टहलने को कहिए।",
            "किसी से बात करना आपकी ताक़त है, उस पर बोझ नहीं।",
        ],
        keywords=["talk to someone", "friend", "family", "baat karna", "दोस्त", "बात करना"],
    ),
]

CBT_TOOLS = [
    dict(
        id="tool-reframe", title_en="Catch it, check it, change it", title_hi="पकड़िए, परखिए, बदलिए",
        topics=["anxiety", "failure", "self_worth", "exam_pressure", "guilt"],
        steps_en=[
            "Catch the harsh thought exactly as it appears, for example 'I always fail'.",
            "Check it: what facts support it, and what facts go against it?",
            "Change it into a fairer sentence, such as 'I failed this time, and I have also succeeded before'.",
        ],
        steps_hi=[
            "कठोर विचार को ठीक वैसे पकड़िए जैसा वह आता है, जैसे 'मैं हमेशा फेल होता हूँ'।",
            "उसे परखिए: कौन-से तथ्य इसे सही ठहराते हैं और कौन-से इसके खिलाफ़ हैं?",
            "उसे एक निष्पक्ष वाक्य में बदलिए, जैसे 'इस बार मैं असफल रहा, पर पहले मैं सफल भी हुआ हूँ'।",
        ],
        keywords=["negative thoughts", "thinking trap", "always", "never", "हमेशा", "कभी नहीं"],
    ),
    dict(
        id="tool-worst-best-likely", title_en="Worst, best, most likely", title_hi="सबसे बुरा, सबसे अच्छा, सबसे संभावित",
        topics=["anxiety", "fear", "exam_pressure", "overthinking"],
        steps_en=[
            "Write the worst thing you fear might happen.",
            "Write the best thing that might happen.",
            "Now write what is most likely, and one small step you can take for that.",
        ],
        steps_hi=[
            "सबसे बुरी बात लिखिए जिसका आपको डर है।",
            "सबसे अच्छी बात लिखिए जो हो सकती है।",
            "अब वह लिखिए जो सबसे ज़्यादा संभावित है, और उसके लिए एक छोटा कदम।",
        ],
        keywords=["what if", "catastrophe", "worst case", "kya hoga", "अगर ऐसा हुआ"],
    ),
    dict(
        id="tool-tiny-action", title_en="One tiny action", title_hi="एक छोटा-सा कदम",
        topics=["low_motivation", "sadness", "burnout"],
        steps_en=[
            "Pick the smallest useful action, one you could finish in five minutes.",
            "Do only that, such as washing one cup, opening the book, or replying to one message.",
            "Notice that starting changed how you feel, then decide whether to do one more tiny thing.",
        ],
        steps_hi=[
            "सबसे छोटा काम चुनिए जो पाँच मिनट में पूरा हो जाए।",
            "सिर्फ़ वही कीजिए, जैसे एक कप धोना, किताब खोलना या एक संदेश का जवाब देना।",
            "देखिए कि शुरू करने से मन कैसा बदला, फिर तय कीजिए कि एक और छोटा काम करना है या नहीं।",
        ],
        keywords=["procrastination", "start", "stuck", "shuru", "शुरू", "आलस"],
    ),
    dict(
        id="tool-worry-time", title_en="A fixed worry time", title_hi="चिंता के लिए तय समय",
        topics=["overthinking", "anxiety", "sleep"],
        steps_en=[
            "Choose a fifteen-minute slot each day, not near bedtime, as your worry time.",
            "When a worry pops up at other times, jot one word and tell yourself: 'I will think about this at my time'.",
            "At the slot, go through the list and mark what you can act on.",
        ],
        steps_hi=[
            "हर दिन पंद्रह मिनट का एक समय चुनिए, सोने के पास नहीं, यही आपका चिंता-समय है।",
            "दूसरे समय चिंता आए तो एक शब्द लिख लीजिए और खुद से कहिए: 'इस पर मैं अपने समय पर सोचूँगा'।",
            "उस समय सूची देखिए और चिह्नित कीजिए कि किस पर काम किया जा सकता है।",
        ],
        keywords=["worry", "rumination", "soch", "सोच", "चिंता"],
    ),
    dict(
        id="tool-self-compassion", title_en="Speak to yourself like a friend", title_hi="खुद से दोस्त की तरह बात कीजिए",
        topics=["self_worth", "guilt", "failure"],
        steps_en=[
            "Imagine a dear friend in your situation. What would you say to them?",
            "Say those same words to yourself, slowly.",
            "Place a hand on your chest and take one gentle breath.",
        ],
        steps_hi=[
            "सोचिए कि आपका कोई प्यारा दोस्त आपकी जगह होता, तो आप उससे क्या कहते?",
            "वही शब्द धीरे-धीरे खुद से कहिए।",
            "सीने पर हाथ रखिए और एक कोमल साँस लीजिए।",
        ],
        keywords=["self criticism", "kind to yourself", "khud se pyaar", "खुद पर दया", "आत्म-करुणा"],
    ),
    dict(
        id="tool-name-it", title_en="Name the feeling", title_hi="भावना को नाम दीजिए",
        topics=["anger", "sadness", "overwhelm", "anxiety"],
        steps_en=[
            "Pause and ask: what exactly am I feeling? Anger, hurt, fear, tiredness?",
            "Say it quietly: 'This is sadness' or 'This is fear'.",
            "Notice where it sits in your body, and breathe toward that place.",
        ],
        steps_hi=[
            "रुककर पूछिए: मैं असल में क्या महसूस कर रहा हूँ? गुस्सा, चोट, डर या थकान?",
            "धीरे से कहिए: 'यह उदासी है' या 'यह डर है'।",
            "ध्यान दीजिए कि वह शरीर में कहाँ बैठी है, और उसी जगह की ओर साँस भेजिए।",
        ],
        keywords=["feelings", "emotions", "identify", "bhavna", "भावना", "एहसास"],
    ),
    dict(
        id="tool-thought-label", title_en="'I am having the thought that…'", title_hi="'मेरे मन में यह विचार आ रहा है कि…'",
        topics=["overthinking", "self_worth", "fear", "anxiety"],
        steps_en=[
            "Take the painful thought, for example 'I am useless'.",
            "Restate it as: 'I am having the thought that I am useless'.",
            "See the thought as a passing cloud, not a fact, and gently return to what you were doing.",
        ],
        steps_hi=[
            "उस दर्दनाक विचार को लीजिए, जैसे 'मैं किसी काम का नहीं हूँ'।",
            "उसे ऐसे दोहराइए: 'मेरे मन में यह विचार आ रहा है कि मैं किसी काम का नहीं हूँ'।",
            "विचार को गुज़रते बादल की तरह देखिए, सच की तरह नहीं, और धीरे से अपने काम पर लौट आइए।",
        ],
        keywords=["thoughts", "defusion", "negative", "vichar", "विचार"],
    ),
    dict(
        id="tool-basic-needs", title_en="Basic needs check", title_hi="बुनियादी ज़रूरतों की जाँच",
        topics=["overwhelm", "grief", "loneliness", "burnout", "sadness"],
        steps_en=[
            "Ask: have I had water and food today? Have I slept?",
            "Is there a safe, quiet place where I can sit for ten minutes?",
            "Is there one person I can be near or message today?",
        ],
        steps_hi=[
            "पूछिए: क्या आज मैंने पानी पिया और खाना खाया? क्या मैं सोया?",
            "क्या कोई सुरक्षित, शांत जगह है जहाँ मैं दस मिनट बैठ सकूँ?",
            "क्या कोई एक इंसान है जिसके पास मैं आज रह सकूँ या जिसे संदेश भेज सकूँ?",
        ],
        keywords=["care", "self care", "basic", "dekhbhal", "देखभाल"],
    ),
]

STORIES = [
    dict(
        id="story-hare-lion", title_en="The Clever Hare and the Lion", title_hi="चतुर खरगोश और शेर",
        topics=["fear", "anxiety", "overwhelm", "exam_pressure"],
        summary_en="A mighty lion terrorised a forest until the animals agreed to send him one animal each day. When the turn of a small hare came, he did not panic. He walked slowly, thought carefully, and found a clever plan that freed the forest from fear.",
        summary_hi="एक बलशाली शेर ने जंगल में आतंक मचा रखा था, तब जानवरों ने तय किया कि रोज़ एक जानवर खुद उसके पास जाएगा। जब एक छोटे खरगोश की बारी आई, तो वह घबराया नहीं। उसने धीरे-धीरे चलकर शांति से सोचा और एक चतुर उपाय निकाला जिसने जंगल को डर से मुक्त कर दिया।",
        moral_en="A calm mind finds a way where panic finds none. Big fears get smaller when you think step by step.",
        moral_hi="शांत मन वह रास्ता निकाल लेता है जो घबराहट नहीं निकाल पाती। बड़े डर भी कदम-कदम सोचने पर छोटे हो जाते हैं।",
        keywords=["panchatantra", "lion", "hare", "clever", "शेर", "खरगोश"],
    ),
    dict(
        id="story-tortoise-geese", title_en="The Tortoise and the Two Geese", title_hi="कछुआ और दो हंस",
        topics=["anger", "relationships", "guilt"],
        summary_en="Two geese agreed to carry a talkative tortoise to a new lake, holding a stick he bit in the middle, on one condition: do not speak. Crowds below jeered, and the tortoise could not hold back his reply. The moment he opened his mouth, he fell.",
        summary_hi="दो हंसों ने बातूनी कछुए को नई झील तक ले जाने का वादा किया, एक लकड़ी के बीच में कछुआ मुँह से पकड़कर लटक गया, पर शर्त यह थी कि वह बोलेगा नहीं। नीचे भीड़ ने ताने कसे और कछुआ जवाब देने से खुद को रोक न सका। मुँह खोलते ही वह गिर पड़ा।",
        moral_en="Pause before you answer. The urge to react in the moment can cost more than the insult itself.",
        moral_hi="जवाब देने से पहले ठहर जाइए। उस पल प्रतिक्रिया देने की आदत कभी-कभी अपमान से भी महँगी पड़ती है।",
        keywords=["panchatantra", "tortoise", "geese", "kachua", "hans", "कछुआ", "हंस"],
    ),
    dict(
        id="story-monkey-crocodile", title_en="The Monkey and the Crocodile", title_hi="बंदर और मगरमच्छ",
        topics=["relationships", "fear", "anxiety", "self_worth"],
        summary_en="A monkey shared sweet fruit with a crocodile who became his friend. Later the crocodile, pushed by his wife, carried the monkey into the river to betray him. The monkey stayed calm, said his heart was left on the tree, and was brought safely back to the bank. After that he kept his distance from such a friend.",
        summary_hi="एक बंदर अपने मीठे फल एक मगरमच्छ के साथ बाँटता था और दोनों दोस्त बन गए। बाद में मगरमच्छ ने पत्नी के कहने पर बंदर को नदी में ले जाकर धोखा देना चाहा। बंदर शांत रहा, उसने कहा कि उसका दिल तो पेड़ पर ही रह गया है, और सुरक्षित किनारे पर लौट आया। उसके बाद उसने ऐसे दोस्त से दूरी बना ली।",
        moral_en="In a crisis, presence of mind is your best friend, and it is wise to step away from people who do not value you.",
        moral_hi="संकट में सूझ-बूझ ही सबसे अच्छी साथी है, और जो आपकी कद्र नहीं करते उनसे दूरी बनाना समझदारी है।",
        keywords=["panchatantra", "monkey", "crocodile", "betrayal", "बंदर", "मगरमच्छ", "धोखा"],
    ),
    dict(
        id="story-four-friends", title_en="The Four Friends: deer, crow, mouse, tortoise", title_hi="चार मित्र: हिरण, कौआ, चूहा और कछुआ",
        topics=["loneliness", "sadness", "grief", "relationships"],
        summary_en="A deer, a crow, a mouse and a tortoise became close friends. When the deer was caught in a hunter's net, the mouse chewed through the ropes while the crow and the tortoise stood by to help, and together they all escaped danger.",
        summary_hi="एक हिरण, कौआ, चूहा और कछुआ गहरे मित्र बन गए। जब हिरण शिकारी के जाल में फँस गया, तो चूहे ने रस्सियाँ कुतर दीं और कौआ व कछुआ मदद के लिए साथ खड़े रहे। सबने मिलकर संकट से पार पाया।",
        moral_en="No one has to get through hard times alone. Good friends make a heavy day lighter, and asking for help is itself a kind of courage.",
        moral_hi="कठिन समय अकेले काटना ज़रूरी नहीं। अच्छे दोस्त भारी दिन को हल्का कर देते हैं, और मदद माँगना खुद एक तरह की हिम्मत है।",
        keywords=["panchatantra", "friends", "friendship", "dost", "mitra", "दोस्त", "मित्र"],
    ),
]
