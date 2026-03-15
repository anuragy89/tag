"""
messages.py – Large, easily-extensible message template library.

Every list can be extended freely.  The helper `get_msg()` picks
a random entry so tagging always feels fresh.
"""

import random
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
#  1.  HITAG  –  Hindi only  (funny + flirty + normal)
# ══════════════════════════════════════════════════════════════════════════════
HITAG_MSGS = [
     "अरे {mention} भाई! VC खुली है, बस तू आ जा — हम तेरा ही इंतज़ार कर रहे थे! 🎙️🔥",
     "{mention} यार VC में सब हैं, बस तू miss है! आ जा, बात करते हैं! 🎧💬",
     "ओए {mention}! अभी VC join कर — मज़ा बहुत आ रहा है, तू रह जाएगा तो पछताएगा! 🎤😂",
     "{mention} bhai VC में आ, नहीं तो सब तेरे बारे में बात कर रहे हैं 😏 सच में! 👀🎙️",
     "यार {mention}! mic on कर, VC में आ — आज की रात epic होने वाली है! 🔥🎧",
     "{mention} VC में तेरी आवाज़ सुनना चाहते हैं यार! एक बार आ तो सही! 🙏🎤",
     "अरे {mention}! VC खाली लग रही है तेरे बिना — भर दे इसे अपनी आवाज़ से! 🎵😄",
     "{mention} भाई headphones लगा और VC join कर — एकदम झक्कास session चल रहा है! 🎧🔥",
     "अरे {mention} भाई! तू कहाँ गायब है? 😜 ग्रुप याद कर रहा था तुझे! 💕",
     "ओए {mention}! सो रहे हो क्या? 😴 उठो उठो, ग्रुप में आओ! 🔔",
     "{mention} जी, आपकी याद आई तो बुला लिया 😍 अब मत जाना! 🙏",
     "भाई {mention}, तू ऑनलाइन क्यों नहीं है? 🤔 हम बिना तेरे अधूरे हैं! 💔",
     "{mention} आ जा यार, बहुत बोर हो रहा हूँ 😩 तू होता है तो मज़ा आता है! 🎉",
     "अरे {mention}! कहाँ हो भई? 👀 ग्रुप में लाश की तरह पड़े हो 😂",
     "{mention} तुझे देखकर दिल खुश हो जाता है 😊 आ जा यार! 🌟",
     "यार {mention}, तू बिना बताये गायब हो गया? 😡 आ सामने! 👊",
     "{mention} जी! नमस्ते 🙏 आज कैसा महसूस कर रहे हो? बताओ! 😄",
     "भई {mention}, इश्क में गिरफ्तार हो गए क्या? 💘 ग्रुप में भी आओ! 😂",
     "{mention} ओ मेरे दिल के चैन 💓 कहाँ हो? ग्रुप तेरे बिना सूना है 😢",
     "अरे भाई {mention}! टैग किया तो कम से कम रिप्लाई तो दो 😤 वरना गुस्सा हो जाऊँगा! 😠",
     "{mention} तू है तो महफ़िल है वरना सब बेकार है 🥺 आ जा ना! 💫",
     "भाई {mention}, ग्रुप का सितारा कब चमकेगा? ⭐ आ जा अब! 😄",
     "{mention} जी आपको बहुत याद किया जा रहा है 🫶 दर्शन दो! 😂",
     "ओए {mention}! फ़ोन रख, ग्रुप में आ 📵 यहाँ भी लोग हैं तेरे! 😜",
     "{mention} यार सुन, तू नहीं आया तो हम सब चले जाएँगे 😂 अब तो आ! 🏃",
     "भई {mention}! इस ग्रुप में तेरी बहुत जरूरत है 🌈 आ जा जल्दी! 💨",
     "{mention} किसी की याद में खोये हो? 😏 हम भी तो हैं यहाँ! 😘",
     "यार {mention}, तू आएगा तो सब खुश हो जाएंगे 🎊 अभी आ! 😆",
     "{mention} भाई! टैग देख के भी नहीं आए? दिल तोड़ दिया 💔 आओ ना! 🥺",
     "अरे {mention}! हम इंतज़ार कर रहे हैं 🕐 जल्दी आओ! 🏃‍♂️",
     "{mention} जी, तुम्हारी एक झलक के लिए तरस रहे हैं 😍 आओ! 🌺",
     "भाई {mention}! ग्रुप में आ, नहीं तो मैं रोने लगूँगा 😭 Kidding! 😂 लेकिन आ जा!",
     "{mention} तेरे जैसा कोई नहीं इस ग्रुप में 🏆 इसीलिए बुला रहा हूँ! 😊",
     "{mention} तेरी एक झलक के लिए तरस रहे हैं — आ जा ना यार! 🥺💫",
     "यार {mention}, तू होता है तो ग्रुप में जान आ जाती है 💯 Miss you! 💕",
     "{mention} जी, आपको बुला रहे हैं — आईए, आपका इंतज़ार है! 🌟🙏",
     "अरे {mention}! तू smile करता है तो group खुश हो जाता है — ab smile karo aur aao! 😊💖",
     "{mention} तू है तो महफ़िल है — बिना तेरे सब अधूरा लगता है! 🎊🫶",
     "{mention} tumhara andaaz nirala hai — isliye personally tag kiya! 😘✨",
     "{mention} यार! तू कहाँ गायब है? ग्रुप में lash की तरह शांत बैठा है 😂 कुछ तो बोल!",
     "अरे {mention}! seen करके चला गया? Bhai ye dil pe lagte hain 💔 Wapas aa yaar! 😂",
     "{mention} तू online है और reply नहीं? यह तो personal attack है भाई! 😤😂",
     "भई {mention}! तुझे tag करना पड़ा माने तू बहुत आलसी है 😂 Come on, uth ja!",
]

# ══════════════════════════════════════════════════════════════════════════════
#  2.  ENTAG  –  English only  (funny + flirty + normal)
# ══════════════════════════════════════════════════════════════════════════════
ENTAG_MSGS = [
    "Hey {mention}! Where have you been hiding? 👀 The group misses you! 💕",
    "{mention} bestie! Stop ignoring us 😤 We see you online! 😂",
    "Paging {mention}! Your presence is required immediately 📢 Don't make us beg! 🙏",
    "Oi {mention}! Wake up, sleeping beauty! 😴 The group needs your energy! ✨",
    "{mention} you absolute legend 🏆 Get in here and bless us with your presence! 👑",
    "Hey {mention}! Are you lost? 😅 Come back to reality – we're here! 🌍",
    "{mention} darling 💖 We've been waiting for you forever. Just saying! 😘",
    "Excuse me {mention}? Yeah you. Come here. 😏 We need to talk. (It's fun, promise!) 🎉",
    "{mention} why are you so quiet lately? 🤫 The group is getting worried! 🥺",
    "Hello there {mention}! Fancy seeing your name here haha 😂 Come chat! 💬",
    "{mention} you traitor! How dare you ghost us 😩 Come back instantly! 💔",
    "Tag! You're it, {mention}! 🏷️ Now it's your turn to be active! 😄",
    "{mention} the vibes are OFF without you 🫶 Please come fix them! 🔧",
    "Good news, {mention}! You've been personally selected to join this chat 😂 Come! 🎊",
    "{mention} babe 💅 the group isn't the same without you. Facts. 💯",
    "PSST! {mention}! Over here! 👋 Yes, YOU! Come join us! 🥳",
    "{mention} I bet you're smiling right now 😊 Now come share that smile with us! 😁",
    "Alert! Alert! {mention} has been detected offline! 🚨 Activating tag protocol! 📡",
    "{mention} you're literally the missing puzzle piece here 🧩 Get in here! 🏃",
    "Hey {mention}! Life is short, come be chaotic with us 🤪 No refunds though! 😂",
    "{mention} your fan club is waiting 🙋‍♂️🙋‍♀️ Please don't keep them waiting! 💫",
    "Knock knock {mention}! Who's there? Your entire group 😂 Open up! 🚪",
    "{mention} we literally googled 'how to summon someone' and tagging was step 1 😅",
    "Dear {mention}, consider this your official VIP invitation 🎟️ Come on in! 🌟",
    "{mention} if you don't reply I'm calling it ghosting and filing a complaint 😤😂",
    "Psst {mention}! VC is open and it's LIVE! Get in here, we need your energy! 🎙️🔥",
    "{mention}! Voice chat is going OFF right now — jump in before you miss out! 🎧⚡",
    "Hey {mention}! Hop in the VC — we're waiting on you specifically! 🎤👑",
    "{mention} the VC isn't complete without your voice fr fr! Join now! 🎙️💯",
    "URGENT: {mention} is needed in VC immediately! 🚨🎧 (it's actually super fun rn)",
    "{mention} dude! The VC is hot tonight — don't be the one who missed it! 🔥🎤",
    "Calling {mention} to the voice chat! 📡 Your signal is strong, now connect! 🎧✨",
    "{mention} we started VC and your seat is literally reserved! Come claim it! 🎙️😄",
    "Hey {mention}! Not to be dramatic but this group genuinely misses you 🥺💖 True story!",
    "{mention} you have main character energy — don't waste it being offline! ✨😘",
    "Dear {mention}, consider this a personal invitation from someone who genuinely wants you here 💕🌟",
    "{mention} your smile probably broke someone's heart today 😏 Now come break our boredom! 😂💖",
    "Okay but {mention} walking into this chat would instantly raise the vibes by 100% 😌🫶",
    "Yoooo {mention}! What's good? Drop in and tell us! 🤙💬",
    "Tag! You're it {mention}! 🏷️ Now you HAVE to respond — those are the rules 😂",
    "{mention} honestly just checking in 💯 You good? Come say hey! 👋",
    "{mention} the squad is assembled, we just need you to complete the lineup! 🫂🔥",
    "Plot twist: {mention} was here all along! 👀 Now make it official and say something! 😂",
    "Attention {mention}! Your vibe is requested in this establishment immediately 🎩✨",
    "{mention} real ones show up — and you're a real one! Prove it! 💪😄",
    "{mention} new day, new chance to not be a ghost! 👻 Take it! 😂🔥",
]

# ══════════════════════════════════════════════════════════════════════════════
#  3.  GMTAG  –  Hinglish Good Morning  (funny + flirty)
# ══════════════════════════════════════════════════════════════════════════════
GMTAG_MSGS = [
    "Good Morning {mention}! ☀️ Uthh jao yaar, zindagi bahut chhoti hai 😂 Aaj kuch toh karo! 🌟",
    "{mention} Good Morning! 🌅 Chai pi lo, life set hai 😄 Aaj ka din tumhara hai! 💪",
    "Subh savere {mention} ko tag karna padta hai 😅 Good Morning bhai! ☀️ Smile karo! 😊",
    "Good Morning {mention}! 🌸 Neend toot gayi? Ab toh uthh jao yaar 😂 We're waiting! 👀",
    "{mention} wakey wakey! 🔔 Good Morning! Sun nikal aaya, tum kab nikloge? 😜☀️",
    "Arre {mention}! Good Morning 🌞 Bhai subha subha miss kiya tumhe! 😍",
    "{mention} good morning! 🌺 Aaj ka din super duper amazing ho tumhara! 💫 Bas active raho! 😄",
    "Rise and shine {mention}! ⭐ Good Morning! Uthh ke group mein aao na please! 🙏😂",
    "{mention} GM! 🌈 Aaj tum bahut cute lag rahe ho (invisibly 😂) Good Morning! 💕",
    "Hey {mention}! Good morning! 🌻 Subah ki pehli tag tujhe hi dedi 😘 Special feel karo! 😁",
    "{mention} GM bhai! ☕ Chai ya coffee? Jaldi batao aur group mein active ho jao! 😄",
    "Good morning {mention}! 🌷 Kal raat soya tha ya phone chalata raha? 😏 Bata bata! 😂",
    "{mention} Good Morning! 🦋 Aaj kuch naya karo, khud ko surprise karo! 🌟 We believe in you!",
    "Subah bhai {mention} ko poora pyaar! 🥰 Good Morning! Smile with teeth today! 😁",
    "{mention}!! Good Morning!! 🎉 Today is going to be EPIC! Trust me! ✨ Ab uth jao! 😂",
    "GM {mention}! 🌝 Raat bhar kya sapne dekhe? Humein bhi batao! 😂 Good morning! 🌅",
    "{mention} Good Morning! 🌼 Ek kaam karo – uthho, smile karo aur group mein aao! 🔥",
    "Subh Prabhat {mention} ji! 🙏 Good Morning! Bhagwan kare aaj ka din best ho! 🌟😄",
    "{mention} GM! ☀️ Neend aachi aayi? Ya phir raat bhar group scroll karte rahe? 😂💕",
    "Hey {mention}! 🌸 Good morning! Tum khush ho toh duniya khush hai! 😊 Smile karo! ✨",
    "Good Morning {mention}! ☀️ Chai pi lo aur VC join karo — subah ki baatein best hoti hain! 🎙️😄",
    "{mention} GM! 🌅 Aaj subah VC karein? Neend bhi bhaag jaayegi aur maza bhi aayega! 🎧🔥",
    "Rise & shine {mention}! ⭐ Subah ki pehli VC tere saath? Headphones lagao! 🎤☀️", 
    "{mention} Good Morning! ☀️ Phone alarm snooze kiya na? Uthh jao yaar, hum hain na! 😂🔔",
    "Subah bhai {mention} ko tag karna padta hai 😂 GM! Neend kaafi thi ya aur chahiye? 😴☕",
    "{mention} GM! 🌞 Sapne mein bhi group yaad aaya? Aao, sach mein aa jao! 😂💬",
    "Good Morning {mention}! 🌺 Raat bhar Netflix dekha? Ab idhar dekho! 😏😄",
    "{mention} GM yaar! ☀️ Uthh ke pehla kaam — group mein active hona! 😂 Chai baad mein! ☕",
    "{mention} wakey wakey! 🔔 Uthh jao — subah ho gayi! Aaj ke plans kya hain? Bataoo! 😄🌸",
    "GM {mention}! ⚡ Aaj energy full charge hai — let's GO! Kya plan hai? 🔥🚀",
    "{mention} GOOD MORNING! 🎉 Aaj ka din EPIC hoga — bass believe karo aur shuru karo! 💯🌅",
    "Good Morning {mention}! 💥 Aaj kuch naya try karo — darr gaye toh bolo, hum saath hain! 😄🫶",
    "{mention} GM! 🌈 Subah ki pehli tag sirf khaas logon ko milti hai — aur tum ho khaas! 👑☀️",
    "{mention} good morning! 😌 Aaj ka vibe? Relaxed ya hustling? Bataao! 💬🌅",
    "Hey {mention}! ☀️ Subah ki sabse meethi cheez hai — tumhe tag karna! 😂 GM bhai! 🌸",
    "GM {mention}! 🌝 Raat kaisi gayi? Neend aachi aayi? Subah ka scene kya hai? 😄",
    "{mention} good morning! 🌷 Aaj group mein active rehna — shaam ko stats dekhenge! 😂📊",
    "Good morning {mention}! ☀️ Naya din, naya chance — aaj kuch badal ke dikhaao! 💫🔥",
    "{mention} GM! 🌤️ Sab kuch theek ho jaata hai — ek achhi subah ke baad! Enjoy it! 😊",
    "Subah bhai! {mention} ☀️ Pehle hi tag kar diya — baaki din apna hai! 😂 GM! 🌟",
    "Good morning {mention}! 🌅 Log kehte hain subah ka time golden hota hai — toh shine karo! ✨",
    "{mention} GM! 🌞 Aaj bhot saari khushiyaan hain tere intezaar mein — bas door mat jaana! 💕🌸",
]

# ══════════════════════════════════════════════════════════════════════════════
#  4.  GNTAG  –  Hinglish Good Night  (funny + flirty)
# ══════════════════════════════════════════════════════════════════════════════
GNTAG_MSGS = [
    "Good Night {mention}! 🌙 Aaj ka din kaisa gaya? Kal fir milenge! 😊✨",
    "{mention} so jaao ab! 😴 Good Night! Sapne mein bhi group yaad aaye 😂🌟",
    "GN {mention}! 🌃 Kal phir milenge, tab tak take care! 💕 Meethe sapne! 🌹",
    "{mention} Shubh Raatri! 🌙 Kal subah bhi tag karenge, darr mat 😂 Jao so jao! 😴",
    "Good Night {mention}! 🌠 Aaj bhot kaam kiya? Ya phone chalate rahe? 😏 So jao ab! 😂",
    "{mention} GN! 💫 Tum jahan bhi ho, kal phir yahan aana! 🙏 Miss karenge! 🥺",
    "Hey {mention}! Good Night! 🌜 Phone rakh do, neend important hai! 💤 Or raho? 😄",
    "{mention} Raatri Shubh ho! ⭐ Aaj ke liye shukriya group ka hissa hone ke liye 🫶",
    "GN {mention}! 🌙 Sapne mein hum aayenge... just kidding 😂 Sleep well! 😴💕",
    "{mention} abhi bhi jaag rahe ho? 😤 Good Night! So jao please 🙏 Kal baat karte hain!",
    "Good Night {mention}! 🌌 Kal phir ek nayi subah hogi, new energy ke saath! 🌅✨",
    "{mention} GN! 🌛 Aaj bahut hasaye, kal bhi hasana mat bhoolna! 😄💛",
    "Hey {mention}! 🌙 Raat ko phone mat chalana 😅 But agar chala bhi rahe ho, GN! 😂✨",
    "{mention} Good Night! 💙 Duniya ki chinta mat karo, bas aaram karo! 😌🌟",
    "GN {mention}! 🌠 Sapne mein princess/prince ayenge 😏 Jao so jao ab! 😂💕",
    "{mention} Shubh Ratri! 🌙 Kal phir tagenge, ab so jao 😄 Take care! 🫶",
    "Good Night {mention}! 🌃 Aaj group mein active rehne ka shukriya! Miss you already! 💔😂",
    "{mention} GN yaar! 🌜 Khayal rakhna apna! Kal milte hain fresh hokar! 🌟✨",
    "Hey {mention}! 😴 Phone neeche rakh, aankhein band karo, so jao! Good Night! 🌙💤",
    "{mention} GN! 🌌 Aaj ki raat ki sabse special tag tumhe 😘 Meethe sapne! 💫",
    "Good Night {mention}! 🌙 Agar jaag rahe ho toh VC join karo — last session of the night! 🎧😄",
    "{mention} GN! 🌃 Raat ko neend nahi aa rahi? VC open hai — aao baat karte hain! 🎙️💤",
    "GN {mention}! 🌟 Sone se pehle VC mein aao — 10 minute wala plan! Aa jao! 🎤🌙",
    "{mention} abhi bhi jaag rahe ho? 😤 Good Night! So jao please! Kal baat karte hain! 😴",
    "GN {mention}! 🌙 Raat ko phone mat chalana — jk, tum toh chalate hi rahoge 😂 So kab jaoge?",
    "{mention} Good Night! 😂 Phone neeche rakh, aankhein band karo, 3...2...1... still awake na? 😅💤",
    "Arey {mention}! Itni raat ko bhi online? 😏 Theek hai, GN! Sapne mein bhi group yaad rakhna! 😂🌙",
    "{mention} GN yaar! 🌛 Kal subah fresh hokar aana — aur pehle hume 'good morning' bolna! 😂☀️",
    "{mention} bhai! So jao! 😴 Raat ko screen time zero karo — doctor saab ne bola hai 😂 GN! 🌙",
    "Good Night {mention}! 🌠 Aaj ke liye shukriya — kal phir milenge! Take care! 💕✨",
    "{mention} GN! 💫 Tum jahan bhi ho, kal phir yahan aana — miss karenge! 🥺🌙",
    "Hey {mention}! Good Night! 🌜 Aaj bahut kuch hua — kal aur achha hoga! Sleep well! 😊💤",
    "{mention} Shubh Raatri! 🌙 Aaj ke sath ka shukriya — ab rest karo, kal phir! 🫶",
    "GN {mention}! 🌌 Meethe sapne aayein — aur sapne mein bhi group active rahe 😂💕",
    "{mention} Good Night! 🌃 Aaj group mein active rehne ka shukriya — miss you already! 🥺💖",
    "Good Night {mention}! 🌟 Aaj kya achieve kiya? Kuch bhi? Proud hoon tujhse! 💪😊",
    "{mention} GN! ⭐ Rest karo, recharge karo — kal naya level unlock hai! 🎮🔋",
    "Good Night {mention}! 🌙 Kal ka din aur bada hoga — abhi rest lo! 🚀💤",
    "{mention} GN yaar! 💫 Jo bhi hua aaj — kal clean slate hai! Sleep tight! 😌🌃",
    "{mention} GN! 🌛 Raat ko kya dekh rahe ho? Movie? Series? Ya bas scroll? 😂 So jao! 💤",
    "Hey {mention}! 🌙 Phone rakh do na — neend bhi important hai! GN! 😴✨",
    "{mention} Good Night! 🌠 Aaj ki raat ki sabse special tag tumhe — feel karo! 😘💫",
    "GN {mention}! 🌌 Kal kuch naya try karna hai? Plan banao — lekin abhi so jao! 😂💤",
    "{mention} Shubh Ratri! 🌙 Kal bhi active rehna — group tumhara wait karega! 💕",
    "Good Night {mention}! 🌃 Duniya ki chinta kal karna — abhi bas aaram! 😌🌟",
    "GN {mention}! ⭐ Tum ho toh group complete hai — kal bhi rehna! 🫶 Sleep well! 😴",
    "{mention} GN bhai/behen! 🌙 Khyaal rakhna apna! Kal subah milte hain! 🌅💕",
    "{mention} Good Night! 💙 Aaj ke saath ki memories hamesha yaad raheingi! See you tomorrow! 🌟",
]

# ══════════════════════════════════════════════════════════════════════════════
#  5.  TAGALL  –  Hinglish general  (funny + flirt + meme + normal)
# ══════════════════════════════════════════════════════════════════════════════
TAGALL_MSGS = [
    "{mention} bhai! 👀 Idhar aa, group mein kuch interesting ho raha hai! 🎉",
    "Arey {mention}! Group mein life hai, phone mein nahi 😂 Aa jao! 🌟",
    "{mention} teri yaad aayi toh tag kar diya 😂 Ab aaja yaar! 💕",
    "Yo {mention}! 🤙 Kya chal raha hai life mein? Bata na! 😄",
    "{mention} tune abhi tak reply nahi kiya? 😤 Bhai ye kya hua? 😂",
    "Arre yaar {mention}! Tum bina bataye gum ho gaye 😩 Wapas aao! 🙏",
    "{mention} 💀 Bhai/Behen, are you alive? Proof chahiye 😂 React karo!",
    "Listen {mention}! 📣 Ye group tumhare bina incomplete hai! Sach mein! 💯",
    "{mention} main teri waajah se yahan hoon tumhe tag karne 😂 Ab kush ho jao! 😊",
    "Oops! {mention} ka naam aa gaya list mein 😅 Toh aa hi jao na! 🎊",
    "{mention} yaar kitna wait karein? 🕐 Aa jao please! 🥺",
    "Tag! 🏷️ {mention}! Tumhari baari hai active hone ki! 😄 Let's go! 🚀",
    "{mention} bhai FOMO mat lo! 😂 Group mein itna sab ho raha hai! Come fast! ⚡",
    "Kahaan ho {mention}? 🔍 Missing person report filed ho gayi 😂 Aao jaldi!",
    "{mention} tum aate ho toh group mein vibe aati hai 🔥 Aa jao please! 💫",
    "Psst! {mention}! 🤫 Secret baat karni hai... group mein aao 😏 Just kidding! 😂",
    "{mention} bhai, duniya gol hai... lekin tum idhar kyun nahi? 😂 Aa jao yaar!",
    "Attention {mention}! 📢 Your presence is strongly requested here! 👑 Welcome!",
    "{mention} without you this group is like chai without sugar ☕ Come sweetennn it! 😂",
    "Oi oi {mention}! 👋 Kya scene hai? Group mein aao, scene bahut acha hai! 🎭",
    "{mention} tujhe dekhke lagta hai ki life mein kuch achha hai 💖 Aa jaa yaar!",
    "Bhai {mention}! Hum sab yahan hain aur tum wahan? 😤 Aao idhar! 🏃",
    "{mention} ab toh aa jao, baat karte hain 😊 Kitna ignore karoge! 😂💕",
    "Hey hey hey {mention}! 🌟 Bas tag kar raha hoon, aage tum jaano 😂 Love ya! 💖",
    "{mention} this message is 100% made with love and 0% spam 😂 Trust me! 😇",
    "{mention} ji! Namaste 🙏 Kaise hain aap? Group yaad kar raha tha aapko! 😊",
    "Hey {mention}! Bhai kya scene hai life mein? Batao na yaar! 💬😄",
    "{mention} yaar bahut dino se nahi dikha! Sab theek hai? 🥺 Miss you!",
    "Arey {mention} bhai! Kuch toh bolo — ek 'hi' bhi chalega! 😂 We're here! 👋",
    "{mention} tujhe dekhke dil khush ho jaata hai — aa ja yaar! 🌈💕",
    "{mention} bhai! Ye group sirf tere liye hai — toh aa bhi ja! 😂🎉",
    "Sunno {mention}! Hum sab yahan hain — tum kab aaoge? 🕐 Jaldi! 🏃",
    "{mention} ji, ek baar darshan do — bahut kripaa hogi! 🙏😂",
    "Arre {mention}! Chhod do sab kaam — pehle yahan aa, baat karte hain! 💬🔥",
    "{mention} VC open hai ABHI! 🎙️ Chal aa jaa — ek minute bhi kam nahi lega active hone mein! 🔥",
    "Oye {mention}! VC mein sab jam gaye hain — tum kab aa rahe ho? 🎧⚡ Jaldi!",
    "{mention} headphones laga aur VC join kar — aaj ki raat yaadgaar banani hai! 🎤🔥",
    "{mention} bhai! VC mein teri awaaz suni nahi kaafi time se — aa, kuch toh bol! 🎙️💬",
    "CALLING {mention}! 📡 VC frequency: GROUP CHANNEL. Please tune in! 🎧😂",
    "Yo {mention}! Sab VC mein hain — tu bhi aa, akela kyun rehega? 🎤🫂 Join kar!",
    "{mention} VC mein ek baar aa toh — baad mein thanks bologe trust me! 🔥🎙️",
    "{mention} 💀 Bhai/Behen, proof de ki alive ho — ek reaction bhi chalega! 😂",
    "Arey {mention}! Tum seen karke nikle? Ye toh cheating hai yaar! 😤 Wapas aao!",
    "{mention} tera naam list mein aaya — congrats! Prize lene aa jao 😂🏆",
    "Breaking: {mention} spotted online but not active! Authorities alerted 😂🚨",
    "{mention} bhai FOMO hoga baad mein — abhi aa jao! 😂 Trust the process!",
    "Kahaan ho {mention}? 🔍 Group missing person case no. 1 filed! Aao jaldi! 😂",
    "{mention} seen... typing... gone. Classic. 😂 Pls come back yaar! 💀",
    "{mention} itna quiet kyun? Volume badhao — hum sunna chahte hain! 📢😄",
    "{mention} ye tag sirf selected logo ko jaata hai 👑 Tu selected hai — aa ja!",
    "{mention}! Group mein kuch acha ho raha hai — miss mat kar! 🎉🔥 Jump in!",
    "Yo {mention}! Aaj ka vibe check — tum pass ho ya fail? 😂 Reply karo!",
    "{mention} naya topic hai group mein — teri raay chahiye! 💬💡 Bata yaar!",
    "Bhai {mention}! Group mein debate chal rahi hai — side kaunsi loge? 😏🎯 Aa jao!",
    "{mention} kuch naya share karo yaar — memes, news, kuch bhi! 😄📲 Group zinda karo!",
    "Hey {mention}! Poll hai group mein — vote kiya? 🗳️ Teri raay important hai! 💯",
    "{mention} teri yaad aayi toh tag kar diya — ab toh aa jaa yaar! 💕😂",
    "Suno {mention}! Tum nahi hote toh group mein kuch missing lagta hai — seriously! 🥺💫",
    "{mention} tujhe dekhke lag jaata hai ki sab theek hai 🌟 Aa ja, dil khush kar de! 😄",
    "{mention} bhai! Ye group tera doosra ghar hai — ghar yaad aa raha hai? Aa ja! 😂🏠",
    "{mention} yaar tu hai toh vibe hai — bina tere sab boring! 💯🔥 Please come!",
    "{mention} ek sawaal — group mein active rehna easy hai ya hard? 😏 Prove it! 😂",
    "{mention} bhai/behen! Zindagi chhoti hai — waste mat karo being offline! 😂 Come!",
    "Tag! 🏷️ {mention}! Ab tumhari baari hai — kuch kaho, kuch karo! 😄🚀",
    "{mention} duniya gol hai, group bhi gol hai — tum kab aoge circle mein? 😂🌍",
    "Oi {mention}! Aaj group mein aanewala pehla message tumhara hona chahiye tha! 😤😂 Ab aa!",
    "{mention} this message was personally crafted for you 💅 Worth replying to? Definitely! 😂",
    "{mention} bhai! Hum sab ek team hain — team member missing nahi hona chahiye! 🫂⚡",
    "{mention} bina reason ke tag kiya — bas teri yaad aayi! 😂💕 Hi from us!",
    "{mention} ek 'hi' bolo — bas itna kaafi hai! 💬😊 We're waiting!",
    "Arey {mention}! Itne dino baad dikhna kab hoga? 👀 Aaj toh aa jao! 😄🎉",
    "{mention} koi nahi puchh raha था — maine puch liya! 😂 Kya chal raha hai life mein? 💬",
]

# ══════════════════════════════════════════════════════════════════════════════
#  6.  JTAG  –  Hinglish Jokes  (funny + flirty + punny)
# ══════════════════════════════════════════════════════════════════════════════
JTAG_MSGS = [
    "{mention} 😂 Ek banda exam ke pehle bolta hai: 'Bhagwan pe bharosa hai' – Bhagwan: 'Mujh pe mat, book pe kar!' 😂",
    "{mention} Teacher: 'Tum class mein soye kyun?' Student: 'Aap boring the sir!' 😂 Relatable? 😅",
    "Ye joke {mention} ke liye hai 😂 Aadmi ne mirror toda – bola '7 saal bad kismat!' Wife ne suna – boli 'Mujhse shaadi ki, 30 saal bad bhi kismat nahi!' 💀",
    "{mention} sunno! 😂 Wifi ka password maanga ghar pe, uncle bole 'Beta rishte mein aa, tab batate hain!' 🤣",
    "Hahaha {mention}! 😆 Biology teacher: 'Bacteria kahan milte hain?' Student: 'Sir, sabse zyada phone ki screen pe!' 😂 True story!",
    "{mention} 🤣 Ek banda bola: 'Main apna past bhoolna chahta hoon' Doctor: 'To payment mein bhi bhool jaoge?' 💀😂",
    "Joke time {mention}! 😂 Maths: 2+2=4 / English: Two plus two is four / Indian Parent: Yeh 4 kab karega kuch? 😭😂",
    "{mention} 😂 Ek banda driving test mein fail hua 9 baar... Driver bola 'Practice makes perfect' – wo bola 'Mere pedestrians bhi yahi kehte hain!' 💀",
    "Lol {mention} 😂 Student exam mein – 'Describe rain' likha: 'Main nahi jaanta lekin chhat toot rahi thi!' 🤣",
    "{mention} 😂 Doston ke group mein tab tak serious rahein jab tak koi photo share na kare aur sab judge na kare! 😅 Waise tumhara kya haal hai? 😜",
    "Haha {mention}! 🤣 Indian mom ka GPS = Sab kuch jaanti hai lekin ek baar ko yeh nahi puchti 'Khana khaya?' Oops wait – wo toh puchti hi rehti hai! 😂",
    "{mention} funny truth! 😂 Homework karne ke baad jo neend aati hai... woh class mein kyun aati hai? 😴 Science jawaab do!",
    "LOL {mention} 🤣 Bhai ne phone pe game kheli raat bhar – subah papa ne dekha: 'Itni mehnatt padhai mein karo!' Bhai: 😶",
    "{mention} 😂 Desi logic: 'Beta doctor bano' – Beta: 'Kyu?' – 'Kyunki sab kehte hain!' – Beta: 'Toh sab bolo' 😅",
    "Hehe {mention}! 😄 Ek banda marriage ke baad bola: 'Mujhe zindagi mein ek hi darr hai' – kya? – 'Wife ka ek aur number save karna!' 💀😂",
    "{mention} ab hasna mat rokna! 😂 Physics: F = ma / Desi papa: F = Fail = My anger 😅 Run!",
    "Tag alert {mention}! 😂 Akbar-Birbal: 'Birbal, aise do log lao jo kuch na karte hon!' – Birbal laaya – 'Ye doctor aur ye government employee hai!' 💀",
    "Hahhaha {mention}! 😆 Ek banda gym gaya aur bola: 'Mujhe six-pack chahiye!' Trainer: 'Roz aao!' Banda: 'Roz? Main toh photo ke liye aaya tha!' 😂",
    "{mention} 😂 School friends ka group = 24/7 active / Family group = Ek forward aaya, sab ne seen kiya, kisi ne reply nahi kiya 😅",
    "{mention} ye joke genuine nahi hai lekin tag genuine hai! 😂 Ab toh bol do kuch! 🗣️💬",
    "{mention} 😂 Indian parent logic: 'Beta doctor bano' — Beta: 'Kyun?' — 'Kyunki hum keh rahe hain!' — Beta: 😶",
    "{mention} sunno! 😂 Wifi ka password maanga — uncle ne kaha 'pehle rishte mein milne aao!' 🤣 Desi life!",
    "{mention} 😂 School mein teacher: 'Tum class mein soye kyun?' Student: 'Sir, aap itna interesting padhaate hain!' 🤣",
    "Haha {mention}! 😆 Maths: 2+2=4 / English: Two plus two is four / Indian Parent: Ye 4 kab kuch karega? 😭😂",
    "{mention} bhai! 😂 Alarm 6 baje ka lagaaya — snooze 9 baar kiya — bola 'neend nahi aayi' 😴 Relatable?",
    "{mention} 🤣 Desi mom GPS = Sab jaanti hai lekin sirf 'Khana khaya?' daily puchti hai! 😂 Love them!",
    "LOL {mention}! 😂 Homework deadline = Raat 11:59 / Netflix binge = Raat 3am / Next day: 'padhai hard hai!' 😅",
    "{mention} 😂 Indian wedding mein relative: 'Beta mota ho gaya!' — ye compliment hai ya roast? 😂 Samajh nahi aata!",
    "Hehe {mention}! 😄 Exam ke pehle din: 'Kal se pakka padhunga' — Exam ke baad: 'Kal se pakka padhunga' 😅 Cycle!",
    "{mention} 😂 Desi logic: 'Ghar pe bata do kahan ja rahe ho' — main to sirf bathroom ja raha tha yaar! 😅",
    "{mention} 😂 Me: I'll sleep at 10pm / My brain at 2am: Remember that one embarrassing thing from 2015? 💀",
    "Lmao {mention}! 😂 Group mein 50 log hain — koi baat karo toh 3 reply karte hain! 😅 We are the 3! 💀",
    "{mention} 🤣 Social media: 'Share if you agree!' — Me: *shares* — Also me: wait I didn't even read it 😂",
    "{mention} bhai! 😂 Phone battery: 3% — me: aaj productive rahunga, phone nahi chalaunga — also me: 2% — panics 😅",
    "Haha {mention}! 🤣 Me buying things on sale: 'I'm saving money!' — Bank account: 'Are you though?' 😂💸",
    "{mention} 😂 Introvert life: Makes plans. Gets excited. Plans day arrives. Prays they cancel. They don't cancel. 💀",
    "LOL {mention}! 😂 'I work better under pressure' = I haven't started yet and deadline is tomorrow 😅 Mood?",
    "{mention} real talk 😂 Gym: Day 1 — motivated! Day 2 — sore. Day 3 — 'exercise is overrated anyway' 💀",
    "{mention} 😂 Bhai itna quiet kyun hai group mein? Shy ho ya keyboard toot gayi? 😜 Bolo kuch!",
    "Roast of the day goes to {mention}! 😂 Just kidding! (mostly) — Ab haso aur reply karo! 🤣",
    "{mention} 😂 Teri typing speed itni slow kyun hai? Kya angle se phone pakad ke type karte ho? 😅",
    "{mention} bhai! 😂 Tera 'seen' karke jaana toh personal attack hai — court mein milte hain! 😤😂",
    "Aye {mention}! 😂 Jo group mein kam bolte hain wo ya toh bahut samajhdar hote hain ya bahut lazy — guess which one you are? 😏",
    "{mention} 😂 Maine ek joke soch ke rakha tha — bhool gaya. Exactly meri zindagi jaisi! 😅",
    "Hey {mention}! 😄 Ek banda bola 'Main waqt nahi barbaad karta!' — Phir bhi 3 ghante YouTube pe gaya 😂 Same?",
    "{mention} 🤣 Life mein do hi cheezein sure hain — tax aur wo dost jo message read karke reply nahi karta! 😂 Tum nahi ho wo! (hopefully)",
    "{mention} sunno! 😂 Optimist: glass half full / Pessimist: glass half empty / Indian parent: 'Glass khareed ne ke paise kahan se aaye?' 😅",
    "{mention} bhai! 🤣 Gym jaane ke baad jo feeling aati hai na — woh next 3 din tak nahi jaane ki bhi aati hai 😂 Back pain zindabad!",
    "{mention} 😂 VC mein 'Haan haan main sun raha hoon' bolke actually kya karte ho? Hum jaante hain! 😏 Scroll kar rahe the na?",
    "Lol {mention}! 🤣 VC mein mic on karke khaana khana aur phir boolna 'main nahi tha' — classic move! 😂 Caught!",
    "{mention} 😂 VC mein sabse zyada bolta hai wo banda jiska mic sab mute kar dete hain 😅 Present in chat!",
    "Haha {mention}! 😆 VC join kiya, 5 min silent baithe, bina bolnye nikle — elite level lurking! 💀 Same? 😂",
    "{mention} 🤣 VC mein 'mera internet slow hai' = 'main kuch nahi bolna chahta but sunna chahta hoon' 😂 We know!",
    "{mention} bhai! 😂 Raat 2 baje VC — subah 6 baje office — ye conversation kuch aur hi jagah le gayi! 😅 But worth it!",
    "Joke time {mention}! 😂 VC mein join ho, sab ko 'hello' bolo, koi response na aaye — unmute karo... tab aaye! 💀 Classic!",
    "{mention} 🤣 Group mein sab: 'Aaj VC karte hain!' — Raat hoti hai — sab: 'kal pakka!' — next day: repeat! 😂 Same plan, new day!",

]

# ══════════════════════════════════════════════════════════════════════════════
#  7.  ADMIN TAG  –  prefix when tagging admins
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_TAG_PREFIX = "📢 **Admin Alert!** Tagging all admins:\n\n"
ADMIN_TAG_SUFFIX = "\n\n⚠️ _Please attend to the matter above._"

# ══════════════════════════════════════════════════════════════════════════════
#  8.  ALL TAG  –  prefix when tagging everyone
# ══════════════════════════════════════════════════════════════════════════════
ALL_TAG_PREFIX = "**\n\n"
ALL_TAG_SUFFIX = "\n\n"

# ══════════════════════════════════════════════════════════════════════════════
#  Welcome messages
# ══════════════════════════════════════════════════════════════════════════════
GROUP_JOIN_MSG = """
🎉 **Hey everyone! I'm alive and kicking!** 🎉

Thanks for adding me to **{chat_title}**! 🙏

I'm your personal **Tag Bot** – here to keep everyone active and entertained! 🔥

➤ Type /help to see all my commands and start tagging! 🏷️

Let's make this group 🔥🔥🔥
"""

# ══════════════════════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════════════════════
_POOL_MAP = {
    "hitag":  HITAG_MSGS,
    "entag":  ENTAG_MSGS,
    "gmtag":  GMTAG_MSGS,
    "gntag":  GNTAG_MSGS,
    "tagall": TAGALL_MSGS,
    "jtag":   JTAG_MSGS,
}

def get_msg(tag_type: str, mention: str, custom: str = "") -> str:
    """Return a random message for *tag_type*, mention substituted in."""
    pool = _POOL_MAP.get(tag_type, TAGALL_MSGS)
    template = random.choice(pool)
    msg = template.format(mention=mention)
    if custom:
        msg = f"{custom}\n\n{msg}"
    return msg


def build_mention(user_id: int, name: str) -> str:
    return f"[{name}](tg://user?id={user_id})"
