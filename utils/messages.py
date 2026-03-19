"""
messages.py – 200 fresh, cool, VC-engaging message templates.

Distribution:
  HITAG   – 34 Hindi msgs
  ENTAG   – 34 English msgs
  GMTAG   – 28 Good Morning Hinglish
  GNTAG   – 28 Good Night Hinglish
  TAGALL  – 38 Hinglish general + VC
  JTAG    – 38 Hinglish jokes + roasts
  Total   = 200
"""

import random
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
#  1.  HITAG  –  Hindi  (funny · flirty · VC-engaging · desi vibes)
# ══════════════════════════════════════════════════════════════════════════════
HITAG_MSGS = [
    # ── VC pull ──
    "अरे {mention} भाई! VC खुली है, बस तू आ जा — हम तेरा ही इंतज़ार कर रहे थे! 🎙️🔥",
    "{mention} यार VC में सब हैं, बस तू miss है! आ जा, बात करते हैं! 🎧💬",
    "ओए {mention}! अभी VC join कर — मज़ा बहुत आ रहा है, तू रह जाएगा तो पछताएगा! 🎤😂",
    "{mention} bhai VC में आ, नहीं तो सब तेरे बारे में बात कर रहे हैं 😏 सच में! 👀🎙️",
    "यार {mention}! mic on कर, VC में आ — आज की रात epic होने वाली है! 🔥🎧",
    "{mention} VC में तेरी आवाज़ सुनना चाहते हैं यार! एक बार आ तो सही! 🙏🎤",
    "अरे {mention}! VC खाली लग रही है तेरे बिना — भर दे इसे अपनी आवाज़ से! 🎵😄",
    "{mention} भाई headphones लगा और VC join कर — एकदम झक्कास session चल रहा है! 🎧🔥",

    # ── Funny ──
    "{mention} यार! तू कहाँ गायब है? ग्रुप में lash की तरह शांत बैठा है 😂 कुछ तो बोल!",
    "अरे {mention}! seen करके चला गया? Bhai ye dil pe lagte hain 💔 Wapas aa yaar! 😂",
    "{mention} तू online है और reply नहीं? यह तो personal attack है भाई! 😤😂",
    "भई {mention}! तुझे tag करना पड़ा माने तू बहुत आलसी है 😂 Come on, uth ja!",
    "{mention} proof bhej ki alive hai — warna missing report file karni padegi! 😂🔍",
    "Yo {mention}! Tera naam list mein aaya — congrats! Ab aa bhi ja 😂🏆",
    "{mention} bhai itna quiet kyun hai? Volume badhao yaar! 📢😄",

    # ── Flirty / Warm ──
    "{mention} तेरी एक झलक के लिए तरस रहे हैं — आ जा ना यार! 🥺💫",
    "यार {mention}, तू होता है तो ग्रुप में जान आ जाती है 💯 Miss you! 💕",
    "{mention} जी, आपको बुला रहे हैं — आईए, आपका इंतज़ार है! 🌟🙏",
    "अरे {mention}! तू smile करता है तो group खुश हो जाता है — ab smile karo aur aao! 😊💖",
    "{mention} तू है तो महफ़िल है — बिना तेरे सब अधूरा लगता है! 🎊🫶",
    "{mention} tumhara andaaz nirala hai — isliye personally tag kiya! 😘✨",

    # ── Motivational/Energy ──
    "{mention} भाई! आज का दिन तेरा है — ग्रुप में आ और energy दिखा! ⚡🔥",
    "अरे {mention}! कुछ बड़ा करने का वक्त आ गया — शुरुआत यहाँ से कर! 💪🚀",
    "{mention} yaar, tu jo bhi kare — 100% karta hai! Aaj bhi isi energy se aa! 🎯💯",
    "Bhai {mention}! Tere jaisa koi nahi iss group mein — seriously! 🏆 Come show up! 😄",

    # ── Classic/Normal ──
    "{mention} ji! Namaste 🙏 Kaise hain aap? Group yaad kar raha tha aapko! 😊",
    "Hey {mention}! Bhai kya scene hai life mein? Batao na yaar! 💬😄",
    "{mention} yaar bahut dino se nahi dikha! Sab theek hai? 🥺 Miss you!",
    "Arey {mention} bhai! Kuch toh bolo — ek 'hi' bhi chalega! 😂 We're here! 👋",
    "{mention} tujhe dekhke dil khush ho jaata hai — aa ja yaar! 🌈💕",
    "{mention} bhai! Ye group sirf tere liye hai — toh aa bhi ja! 😂🎉",
    "Sunno {mention}! Hum sab yahan hain — tum kab aaoge? 🕐 Jaldi! 🏃",
    "{mention} ji, ek baar darshan do — bahut kripaa hogi! 🙏😂",
    "Arre {mention}! Chhod do sab kaam — pehle yahan aa, baat karte hain! 💬🔥",
    # 3 bonus to reach 200
    "{mention} bhai ek kaam kar — group mein aa, bas! 😂 Simple instructions! 🎯",
    "{mention} yaar tujhe tag karna meri favourite hobby ban gayi hai 😂 Aa ja please! 💕",
    "{mention} bhai! Jitna phone scroll karte ho utna group mein active raho — deal? 😂🤝",
]


# ══════════════════════════════════════════════════════════════════════════════
#  2.  ENTAG  –  English  (cool · witty · VC pull · Gen-Z vibes)
# ══════════════════════════════════════════════════════════════════════════════
ENTAG_MSGS = [
    # ── VC pull ──
    "Psst {mention}! VC is open and it's LIVE! Get in here, we need your energy! 🎙️🔥",
    "{mention}! Voice chat is going OFF right now — jump in before you miss out! 🎧⚡",
    "Hey {mention}! Hop in the VC — we're waiting on you specifically! 🎤👑",
    "{mention} the VC isn't complete without your voice fr fr! Join now! 🎙️💯",
    "URGENT: {mention} is needed in VC immediately! 🚨🎧 (it's actually super fun rn)",
    "{mention} dude! The VC is hot tonight — don't be the one who missed it! 🔥🎤",
    "Calling {mention} to the voice chat! 📡 Your signal is strong, now connect! 🎧✨",
    "{mention} we started VC and your seat is literally reserved! Come claim it! 🎙️😄",

    # ── Funny/Savage ──
    "{mention} saw the message, left on read, carried on with life. The audacity 😂 come back!",
    "Breaking news: {mention} has been spotted online but not in the group! 🚨 Arrest them! 😂",
    "{mention} babe, being a ghost is so last season 👻 Come haunt us here instead! 😂💅",
    "Hey {mention}! I filed a missing person report. Police said 'have you tried tagging them?' So here we are 😂",
    "{mention} you've been quiet for so long I forgot what your vibe even is 😂 Remind us! 💬",
    "Sir/Ma'am {mention}! This is your third and final notice to appear in the group 😤📩 Act now!",
    "{mention} every time I tag you I age slightly 😂 Worth it tho! Now come! 🏃",

    # ── Hype/Motivational ──
    "{mention} you are literally built different! 💪 Show this group what you got! 🔥",
    "The main character just dropped — it's you {mention}! 🎬✨ Time to perform! 🚀",
    "{mention} no cap, this group needs your specific brand of chaos rn! 😂⚡ Get in here!",
    "Big things happening, {mention}! And you're part of it — just show up! 💫🎯",
    "{mention} the world needs your energy today! Start with us! 🌍🔥 Let's GO!",

    # ── Flirty/Warm ──
    "Hey {mention}! Not to be dramatic but this group genuinely misses you 🥺💖 True story!",
    "{mention} you have main character energy — don't waste it being offline! ✨😘",
    "Dear {mention}, consider this a personal invitation from someone who genuinely wants you here 💕🌟",
    "{mention} your smile probably broke someone's heart today 😏 Now come break our boredom! 😂💖",
    "Okay but {mention} walking into this chat would instantly raise the vibes by 100% 😌🫶",

    # ── Cool/Casual ──
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
#  3.  GMTAG  –  Good Morning Hinglish  (energetic · VC ready · fun)
# ══════════════════════════════════════════════════════════════════════════════
GMTAG_MSGS = [
    # ── VC morning calls ──
    "Good Morning {mention}! ☀️ Chai pi lo aur VC join karo — subah ki baatein best hoti hain! 🎙️😄",
    "{mention} GM! 🌅 Aaj subah VC karein? Neend bhi bhaag jaayegi aur maza bhi aayega! 🎧🔥",
    "Rise & shine {mention}! ⭐ Subah ki pehli VC tere saath? Headphones lagao! 🎤☀️",

    # ── Funny morning ──
    "{mention} Good Morning! ☀️ Phone alarm snooze kiya na? Uthh jao yaar, hum hain na! 😂🔔",
    "Subah bhai {mention} ko tag karna padta hai 😂 GM! Neend kaafi thi ya aur chahiye? 😴☕",
    "{mention} GM! 🌞 Sapne mein bhi group yaad aaya? Aao, sach mein aa jao! 😂💬",
    "Good Morning {mention}! 🌺 Raat bhar Netflix dekha? Ab idhar dekho! 😏😄",
    "{mention} GM yaar! ☀️ Uthh ke pehla kaam — group mein active hona! 😂 Chai baad mein! ☕",
    "{mention} wakey wakey! 🔔 Uthh jao — subah ho gayi! Aaj ke plans kya hain? Bataoo! 😄🌸",

    # ── Warm morning ──
    "Good Morning {mention}! 🌸 Aaj ka din tumhara hai — khush raho, shine karo! ✨💫",
    "{mention} GM! ☕ Chai ya coffee? Jaldi bolo aur bata do! Hum bhi peenge saath mein! 😊",
    "Subh Prabhat {mention} ji! 🙏 Bhagwan kare aaj ka din aapka best day ho! 🌟😊",
    "Good Morning {mention}! 🦋 Ek naya din, ek nayi shuruwaat — chalo kuch zabardast karte hain! 🚀",
    "{mention} GM bhai/behen! 🌼 Aaj khud ko proud karo — chhota sa hi sahi, kuch toh karo! 💪",
    "Hey {mention}! Good morning! 🌻 Tum khush ho toh hum khush hain — so smile karo! 😁✨",

    # ── Energy/Hype ──
    "GM {mention}! ⚡ Aaj energy full charge hai — let's GO! Kya plan hai? 🔥🚀",
    "{mention} GOOD MORNING! 🎉 Aaj ka din EPIC hoga — bass believe karo aur shuru karo! 💯🌅",
    "Good Morning {mention}! 💥 Aaj kuch naya try karo — darr gaye toh bolo, hum saath hain! 😄🫶",
    "{mention} GM! 🌈 Subah ki pehli tag sirf khaas logon ko milti hai — aur tum ho khaas! 👑☀️",

    # ── Chill morning ──
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
#  4.  GNTAG  –  Good Night Hinglish  (sweet · funny · VC wind-down)
# ══════════════════════════════════════════════════════════════════════════════
GNTAG_MSGS = [
    # ── VC wind-down ──
    "Good Night {mention}! 🌙 Agar jaag rahe ho toh VC join karo — last session of the night! 🎧😄",
    "{mention} GN! 🌃 Raat ko neend nahi aa rahi? VC open hai — aao baat karte hain! 🎙️💤",
    "GN {mention}! 🌟 Sone se pehle VC mein aao — 10 minute wala plan! Aa jao! 🎤🌙",

    # ── Funny night ──
    "{mention} abhi bhi jaag rahe ho? 😤 Good Night! So jao please! Kal baat karte hain! 😴",
    "GN {mention}! 🌙 Raat ko phone mat chalana — jk, tum toh chalate hi rahoge 😂 So kab jaoge?",
    "{mention} Good Night! 😂 Phone neeche rakh, aankhein band karo, 3...2...1... still awake na? 😅💤",
    "Arey {mention}! Itni raat ko bhi online? 😏 Theek hai, GN! Sapne mein bhi group yaad rakhna! 😂🌙",
    "{mention} GN yaar! 🌛 Kal subah fresh hokar aana — aur pehle hume 'good morning' bolna! 😂☀️",
    "{mention} bhai! So jao! 😴 Raat ko screen time zero karo — doctor saab ne bola hai 😂 GN! 🌙",

    # ── Sweet/Warm ──
    "Good Night {mention}! 🌠 Aaj ke liye shukriya — kal phir milenge! Take care! 💕✨",
    "{mention} GN! 💫 Tum jahan bhi ho, kal phir yahan aana — miss karenge! 🥺🌙",
    "Hey {mention}! Good Night! 🌜 Aaj bahut kuch hua — kal aur achha hoga! Sleep well! 😊💤",
    "{mention} Shubh Raatri! 🌙 Aaj ke sath ka shukriya — ab rest karo, kal phir! 🫶",
    "GN {mention}! 🌌 Meethe sapne aayein — aur sapne mein bhi group active rahe 😂💕",
    "{mention} Good Night! 🌃 Aaj group mein active rehne ka shukriya — miss you already! 🥺💖",

    # ── Motivational wind-down ──
    "Good Night {mention}! 🌟 Aaj kya achieve kiya? Kuch bhi? Proud hoon tujhse! 💪😊",
    "{mention} GN! ⭐ Rest karo, recharge karo — kal naya level unlock hai! 🎮🔋",
    "Good Night {mention}! 🌙 Kal ka din aur bada hoga — abhi rest lo! 🚀💤",
    "{mention} GN yaar! 💫 Jo bhi hua aaj — kal clean slate hai! Sleep tight! 😌🌃",

    # ── Chill night ──
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
#  5.  TAGALL  –  Hinglish general + VC engaging  (hype · fun · meme)
# ══════════════════════════════════════════════════════════════════════════════
TAGALL_MSGS = [
    # ── VC hype ──
    "{mention} VC open hai ABHI! 🎙️ Chal aa jaa — ek minute bhi kam nahi lega active hone mein! 🔥",
    "Oye {mention}! VC mein sab jam gaye hain — tum kab aa rahe ho? 🎧⚡ Jaldi!",
    "{mention} headphones laga aur VC join kar — aaj ki raat yaadgaar banani hai! 🎤🔥",
    "{mention} bhai! VC mein teri awaaz suni nahi kaafi time se — aa, kuch toh bol! 🎙️💬",
    "CALLING {mention}! 📡 VC frequency: GROUP CHANNEL. Please tune in! 🎧😂",
    "Yo {mention}! Sab VC mein hain — tu bhi aa, akela kyun rehega? 🎤🫂 Join kar!",
    "{mention} VC mein ek baar aa toh — baad mein thanks bologe trust me! 🔥🎙️",

    # ── Meme/Funny ──
    "{mention} 💀 Bhai/Behen, proof de ki alive ho — ek reaction bhi chalega! 😂",
    "Arey {mention}! Tum seen karke nikle? Ye toh cheating hai yaar! 😤 Wapas aao!",
    "{mention} tera naam list mein aaya — congrats! Prize lene aa jao 😂🏆",
    "Breaking: {mention} spotted online but not active! Authorities alerted 😂🚨",
    "{mention} bhai FOMO hoga baad mein — abhi aa jao! 😂 Trust the process!",
    "Kahaan ho {mention}? 🔍 Group missing person case no. 1 filed! Aao jaldi! 😂",
    "{mention} seen... typing... gone. Classic. 😂 Pls come back yaar! 💀",
    "{mention} itna quiet kyun? Volume badhao — hum sunna chahte hain! 📢😄",
    "{mention} ye tag sirf selected logo ko jaata hai 👑 Tu selected hai — aa ja!",

    # ── Engagement/Hype ──
    "{mention}! Group mein kuch acha ho raha hai — miss mat kar! 🎉🔥 Jump in!",
    "Yo {mention}! Aaj ka vibe check — tum pass ho ya fail? 😂 Reply karo!",
    "{mention} naya topic hai group mein — teri raay chahiye! 💬💡 Bata yaar!",
    "Bhai {mention}! Group mein debate chal rahi hai — side kaunsi loge? 😏🎯 Aa jao!",
    "{mention} kuch naya share karo yaar — memes, news, kuch bhi! 😄📲 Group zinda karo!",
    "Hey {mention}! Poll hai group mein — vote kiya? 🗳️ Teri raay important hai! 💯",

    # ── Warm/Emotional ──
    "{mention} teri yaad aayi toh tag kar diya — ab toh aa jaa yaar! 💕😂",
    "Suno {mention}! Tum nahi hote toh group mein kuch missing lagta hai — seriously! 🥺💫",
    "{mention} tujhe dekhke lag jaata hai ki sab theek hai 🌟 Aa ja, dil khush kar de! 😄",
    "{mention} bhai! Ye group tera doosra ghar hai — ghar yaad aa raha hai? Aa ja! 😂🏠",
    "{mention} yaar tu hai toh vibe hai — bina tere sab boring! 💯🔥 Please come!",

    # ── Random fun ──
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
#  6.  JTAG  –  Hinglish Jokes + Roasts  (savage · clean · relatable)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  7.  VCTAG  –  VC invite  (funny · flirty · hype · desi)
# ══════════════════════════════════════════════════════════════════════════════
VCTAG_MSGS = [
    # ── Flirty invites ──
    "{mention} aaja VC mein, teri awaaz sunne ka dil kar raha hai 😍🎙️",
    "{mention} VC mein aa na yaar, tere bina baatein adhuri lagti hain 🥺🎧",
    "Aye {mention}! VC open hai — aaja, hum wait kar rahe hain sirf tere liye 😘🎤",
    "{mention} teri awaaz VC ka sabse achha part hogi 💖 Aa ja na please! 🎙️",
    "{mention} darling! VC mein itna maza aa raha hai — tere bina sab pheeka hai 😩🎧",

    # ── Funny invites ──
    "{mention} VC join kar varna hum tera gossip karenge 😂🗣️ Choice teri hai!",
    "Oye {mention}! VC mein aa — warna sochenge tu busy hai kisi aur group mein 😏😂",
    "{mention} VC mein itne log hain aur tu nahi? Sharam nahi aati? 😂 Jaldi aa!",
    "{mention} headphones laga, mic on kar, aur VC mein bomb gira de 💣😂🎤",
    "BREAKING NEWS: {mention} abhi bhi VC join nahi kiya! Poori duniya shocked hai 😂📢",
    "{mention} bhai VC mein aa — promise karta hoon roast nahi karunga 😇 (maybe) 😂",
    "{mention} VC join kar, warna kal bhi tag karunga, parso bhi, aur hamesha bhi 😂🔁",

    # ── Hype invites ──
    "{mention} aaja VC mein! Aaj ki raat epic hone wali hai 🔥🎙️ Miss mat kar!",
    "{mention} VC live hai ABHI! 🔴 Sab wait kar rahe hain — aa ja ek minute mein! ⚡",
    "YO {mention}! VC mein vibe ekdum fire hai 🔥 Tu aayega toh aur bhi lit ho jaega! 🎧",
    "{mention} VC mein aa — aaj kuch aisa hoga jo yaad rahega 🎉🎙️ Trust me!",
    "Calling {mention} to the main stage! 🎤 VC ready hai, audience ready hai — bas TU nahi! 😂",

    # ── Desi style ──
    "{mention} yaar! VC khuli hai, chai bhi ban rahi hai — aa ja baithte hain! ☕🎙️",
    "{mention} VC mein aa bhai — idhar baat karte hain, group mein toh sirf forward hote hain 😂🎧",
    "Arre {mention}! Kitna sona hai? VC mein subah ki mehfil jam rahi hai ☀️🎤 Uth bhi ja!",
    "{mention} VC mein aake ek baar bata toh — kya scene hai life mein? 💬🎙️ Hum sab curious hain!",
    "{mention} bhai/behen! VC mein itna maza aa raha hai ke battery bhi bhool gayi drain hona 😂🔋🎧",

    # ── Short punchy ──
    "{mention} VC. Now. Please. 🎙️🙏",
    "{mention} MIC ON KAR! 🎤🔥 VC wait kar rahi hai!",
    "{mention} ek minute bhi chalega — aa ja VC mein! ⏱️🎧",
]

JTAG_MSGS = [
    # ── Relatable desi jokes ──
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

    # ── Gen-Z / internet jokes ──
    "{mention} 😂 Me: I'll sleep at 10pm / My brain at 2am: Remember that one embarrassing thing from 2015? 💀",
    "Lmao {mention}! 😂 Group mein 50 log hain — koi baat karo toh 3 reply karte hain! 😅 We are the 3! 💀",
    "{mention} 🤣 Social media: 'Share if you agree!' — Me: *shares* — Also me: wait I didn't even read it 😂",
    "{mention} bhai! 😂 Phone battery: 3% — me: aaj productive rahunga, phone nahi chalaunga — also me: 2% — panics 😅",
    "Haha {mention}! 🤣 Me buying things on sale: 'I'm saving money!' — Bank account: 'Are you though?' 😂💸",
    "{mention} 😂 Introvert life: Makes plans. Gets excited. Plans day arrives. Prays they cancel. They don't cancel. 💀",
    "LOL {mention}! 😂 'I work better under pressure' = I haven't started yet and deadline is tomorrow 😅 Mood?",
    "{mention} real talk 😂 Gym: Day 1 — motivated! Day 2 — sore. Day 3 — 'exercise is overrated anyway' 💀",

    # ── Savage roasts (clean) ──
    "{mention} 😂 Bhai itna quiet kyun hai group mein? Shy ho ya keyboard toot gayi? 😜 Bolo kuch!",
    "Roast of the day goes to {mention}! 😂 Just kidding! (mostly) — Ab haso aur reply karo! 🤣",
    "{mention} 😂 Teri typing speed itni slow kyun hai? Kya angle se phone pakad ke type karte ho? 😅",
    "{mention} bhai! 😂 Tera 'seen' karke jaana toh personal attack hai — court mein milte hain! 😤😂",
    "Aye {mention}! 😂 Jo group mein kam bolte hain wo ya toh bahut samajhdar hote hain ya bahut lazy — guess which one you are? 😏",

    # ── Punny / Wordplay ──
    "{mention} 😂 Maine ek joke soch ke rakha tha — bhool gaya. Exactly meri zindagi jaisi! 😅",
    "Hey {mention}! 😄 Ek banda bola 'Main waqt nahi barbaad karta!' — Phir bhi 3 ghante YouTube pe gaya 😂 Same?",
    "{mention} 🤣 Life mein do hi cheezein sure hain — tax aur wo dost jo message read karke reply nahi karta! 😂 Tum nahi ho wo! (hopefully)",
    "{mention} sunno! 😂 Optimist: glass half full / Pessimist: glass half empty / Indian parent: 'Glass khareed ne ke paise kahan se aaye?' 😅",
    "{mention} bhai! 🤣 Gym jaane ke baad jo feeling aati hai na — woh next 3 din tak nahi jaane ki bhi aati hai 😂 Back pain zindabad!",

    # ── Situational / VC jokes ──
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
#  Static tag wrappers
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  Static tag wrappers
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_TAG_PREFIX = "📢 **Admin Alert!** Calling all admins:\n\n"
ADMIN_TAG_SUFFIX = "\n\n"

ALL_TAG_PREFIX   = "\n\n"
ALL_TAG_SUFFIX   = "\n\n"


def GROUP_JOIN_MSG(chat_title: str) -> str:
    """HTML group welcome message with premium emoji via te()."""
    from utils.botapi import te   # local import — avoids circular at module load
    return (
        f"{te('wave','👋')} <b>Heyy {chat_title}!</b>\n\n"
        f"Main hoon <b>Tag Master Bot</b> — aapka naya group assistant! "
        f"{te('robot','🤖')}{te('fire','🔥')}\n\n"
        f"{te('tag','🏷️')} <b>Kya kar sakta hoon:</b>\n"
        f"├ Hindi, English, Hinglish tags\n"
        f"├ Good Morning &amp; Good Night tags\n"
        f"├ Joke tags, VC tags &amp; General tags\n"
        f"├ Sirf admins ko tag karo (<code>@admin</code>)\n"
        f"└ Sab members ko tag karo (<code>@all</code>)\n\n"
        f"{te('lightning','⚡')} <b>Controls:</b> /stop · /pause · /resume\n\n"
        f"{te('crown','👑')} Mujhe <b>admin</b> banao for best experience!\n\n"
        f"➤ /help se dekho poori command list! {te('sparkle','✨')}"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════
_POOL_MAP = {
    "hitag":  HITAG_MSGS,
    "entag":  ENTAG_MSGS,
    "gmtag":  GMTAG_MSGS,
    "gntag":  GNTAG_MSGS,
    "tagall": TAGALL_MSGS,
    "jtag":   JTAG_MSGS,
    "vctag":  VCTAG_MSGS,
}


def get_msg(tag_type: str, mention: str, custom: str = "") -> str:
    """Return a random message for *tag_type* with mention substituted in."""
    pool     = _POOL_MAP.get(tag_type, TAGALL_MSGS)
    template = random.choice(pool)
    msg      = template.format(mention=mention)
    if custom:
        msg = f"{custom}\n\n{msg}"
    return msg


def build_mention(user_id: int, name: str) -> str:
    """Markdown format — used in /hitag /entag /gmtag /gntag /tagall /jtag /all /admin."""
    return f"[{name}](tg://user?id={user_id})"


def build_mention_html(user_id: int, name: str) -> str:
    """HTML format — used in /vctag and any HTML parse_mode message."""
    import html as _html
    safe_name = _html.escape(str(name))
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'
