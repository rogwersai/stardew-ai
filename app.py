from flask import Flask, render_template, request
import csv
import re

app = Flask(__name__)

# -------------------------
# VERİLERİ YÜKLE
# -------------------------

with open("stardew_data.csv", "r", encoding="utf-8") as file:
    data = list(csv.DictReader(file))

with open("crops.csv", "r", encoding="utf-8") as file:
    crops = list(csv.DictReader(file))

with open("fish.csv", "r", encoding="utf-8") as file:
    fish_data = list(csv.DictReader(file))

with open("minerals.csv", "r", encoding="utf-8") as file:
    minerals = list(csv.DictReader(file))


# -------------------------
# YARDIMCI FONKSİYONLAR
# -------------------------

def find_character(question):
    for row in data:
        if row["character"].lower().strip() in question:
            return row
    return None


def find_crop(question):
    for row in crops:
        if row["crop_tr"].lower().strip() in question:
            return row
    return None


def find_fish(question):
    for row in fish_data:
        if row["fish_tr"].lower().strip() in question:
            return row
    return None


def find_mineral(question):
    for row in minerals:
        if row["mineral_tr"].lower().strip() in question:
            return row
    return None


def format_list(items):
    items = [item.strip() for item in items if item.strip()]

    if len(items) == 0:
        return "bu konuda bilgim yok"

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} ve {items[1]}"

    return ", ".join(items[:-1]) + f" ve {items[-1]}"


def crop_profit(row):
    sell_price = float(row["sell_price"])
    seed_price = float(row["seed_price"])

    if row["regrowth_days"] == "0":
        return sell_price - seed_price

    return (sell_price * 2) - seed_price


def get_season_crops(season):
    result = []

    for crop in crops:
        seasons = crop["season"].split("|")

        if season in seasons:
            result.append(crop)

    return result


def best_crop_by_profit(season=None):
    available = crops

    if season:
        available = get_season_crops(season)

    if not available:
        return None

    return max(available, key=crop_profit)


def best_crop_by_price(season=None):
    available = crops

    if season:
        available = get_season_crops(season)

    if not available:
        return None

    return max(
        available,
        key=lambda x: float(x["sell_price"])
    )


def fastest_crop(season=None):
    available = crops

    if season:
        available = get_season_crops(season)

    if not available:
        return None

    return min(
        available,
        key=lambda x: float(x["growth_days"])
    )


def crops_with_budget(budget, season=None):
    available = crops

    if season:
        available = get_season_crops(season)

    affordable = []

    for crop in available:
        seed_price = float(crop["seed_price"])

        if seed_price <= budget:
            affordable.append(crop)

    return affordable


# -------------------------
# ANA SAYFA
# -------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    answer = ""

    if request.method == "POST":

        question = request.form["character"].lower().strip()

        # -------------------------
        # BÜTÇE SORUSU
        # -------------------------

        budget_match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*g",
            question
        )

        if budget_match and (
            "ne ek" in question
            or "hangi ürün" in question
            or "ne al" in question
            or "ekmeliyim" in question
            or "eksem" in question
        ):

            budget = float(
                budget_match.group(1).replace(",", ".")
            )

            season = None

            if "yaz" in question:
                season = "Yaz"

            elif "sonbahar" in question:
                season = "Sonbahar"

            elif "ilkbahar" in question:
                season = "İlkbahar"

            affordable = crops_with_budget(
                budget,
                season
            )

            if affordable:

                best = max(
                    affordable,
                    key=crop_profit
                )

                answer = (
                    f"💰 {budget:.0f}g bütçeyle "
                    f"{best['crop_tr']} iyi bir seçenek. 🌱 "
                    f"Tohumu {best['seed_price']}g, "
                    f"satış fiyatı {best['sell_price']}g "
                    f"ve {best['growth_days']} günde yetişiyor."
                )

            else:

                answer = (
                    f"😔 {budget:.0f}g bütçeyle "
                    "verilerimde uygun bir ürün bulamadım."
                )

            return render_template(
                "index.html",
                answer=answer
            )


        # -------------------------
        # EN KÂRLI
        # -------------------------

        if (
            "en karlı" in question
            or "en çok kar" in question
            or "en fazla kar" in question
            or "en çok para" in question
            or "en fazla para" in question
        ):

            season = None

            if "yaz" in question:
                season = "Yaz"

            elif "sonbahar" in question:
                season = "Sonbahar"

            elif "ilkbahar" in question:
                season = "İlkbahar"

            crop = best_crop_by_profit(season)

            if crop:

                profit = crop_profit(crop)

                answer = (
                    f"🌱 "
                    f"{season + ' için ' if season else ''}"
                    f"en kârlı seçenek "
                    f"{crop['crop_tr']} öne çıkıyor. "
                    f"Tohum fiyatı {crop['seed_price']}g, "
                    f"satış fiyatı {crop['sell_price']}g. "
                    f"Tahmini getirisi yaklaşık "
                    f"{profit:.0f}g."
                )

                return render_template(
                    "index.html",
                    answer=answer
                )


        # -------------------------
        # EN PAHALI
        # -------------------------

        if (
            "en pahalı" in question
            or "en yüksek fiyat" in question
            or "en değerli ürün" in question
        ):

            season = None

            if "yaz" in question:
                season = "Yaz"

            elif "sonbahar" in question:
                season = "Sonbahar"

            elif "ilkbahar" in question:
                season = "İlkbahar"

            crop = best_crop_by_price(season)

            if crop:

                answer = (
                    f"💰 "
                    f"{season + ' için ' if season else ''}"
                    f"en yüksek satış fiyatına sahip "
                    f"ürün {crop['crop_tr']}. "
                    f"Tanesi {crop['sell_price']}g."
                )

                return render_template(
                    "index.html",
                    answer=answer
                )


        # -------------------------
        # EN HIZLI
        # -------------------------

        if (
            "en hızlı" in question
            or "en çabuk" in question
            or "en hızlı yetişen" in question
        ):

            season = None

            if "yaz" in question:
                season = "Yaz"

            elif "sonbahar" in question:
                season = "Sonbahar"

            elif "ilkbahar" in question:
                season = "İlkbahar"

            crop = fastest_crop(season)

            if crop:

                answer = (
                    f"⚡ "
                    f"{season + ' için ' if season else ''}"
                    f"en hızlı yetişen ürün "
                    f"{crop['crop_tr']}. "
                    f"{crop['growth_days']} günde yetişiyor."
                )

                return render_template(
                    "index.html",
                    answer=answer
                )


        # -------------------------
        # NE EKMELİYİM?
        # -------------------------

        if (
            "ne ekmeliyim" in question
            or "ne eksem" in question
            or "ne ekeyim" in question
            or "ne ekmek mantıklı" in question
            or "hangi ürünü ekmeliyim" in question
        ):

            season = None

            if "yaz" in question:
                season = "Yaz"

            elif "sonbahar" in question:
                season = "Sonbahar"

            elif "ilkbahar" in question:
                season = "İlkbahar"

            if season:

                crop = best_crop_by_profit(season)

                answer = (
                    f"🌱 {season} için benim önerim "
                    f"{crop['crop_tr']}. "
                    f"{crop['growth_days']} günde yetişiyor "
                    f"ve {crop['sell_price']}g'a satılıyor. "
                    f"Tohumu {crop['seed_price']}g."
                )

            else:

                answer = (
                    "🌱 Hangi mevsim için öneri istediğini "
                    "söylersen mahsulleri karşılaştırabilirim. "
                    "Örneğin: 'Yazın ne ekmeliyim?'"
                )

            return render_template(
                "index.html",
                answer=answer
            )


        # -------------------------
        # MADEN
        # -------------------------

        mineral = find_mineral(question)

        if mineral:

            mineral_name = mineral["mineral_tr"]
            location = mineral["location"]
            floors = mineral["floors"]
            sell_price = mineral["sell_price"]

            if (
                "hangi kat" in question
                or "hangi katta" in question
                or "kaçıncı kat" in question
                or "kat" in question
            ):

                answer = (
                    f"{mineral_name} genellikle "
                    f"{floors}. katlar arasında bulunuyor. ⛏️"
                )

            elif (
                "nerede" in question
                or "nereden" in question
                or "bulabilirim" in question
            ):

                answer = (
                    f"{mineral_name} "
                    f"{location} bölgesinde bulunabiliyor. 💎"
                )

            elif (
                "kaç altın" in question
                or "ne kadar" in question
                or "fiyat" in question
                or "satış" in question
                or "satılır" in question
            ):

                answer = (
                    f"{mineral_name} "
                    f"{sell_price}g karşılığında satılıyor. 💰"
                )

            else:

                answer = (
                    f"{mineral_name}; "
                    f"{floors}. katlar arasında bulunuyor "
                    f"ve {sell_price}g değerinde. 💎"
                )

            return render_template(
                "index.html",
                answer=answer
            )


        # -------------------------
        # BALIK
        # -------------------------

        fish = find_fish(question)

        if fish:

            fish_name = fish["fish_tr"]
            season = fish["season"]
            location = fish["location"]
            time = fish["time"]
            sell_price = fish["sell_price"]

            if (
                "hangi mevsim" in question
                or "hangi mevsimde" in question
                or "mevsim" in question
            ):

                answer = (
                    f"{fish_name} "
                    f"{season} döneminde yakalanabiliyor. 🐟"
                )

            elif (
                "nerede" in question
                or "hangi yerde" in question
                or "nereden" in question
            ):

                answer = (
                    f"{fish_name} şu bölgelerde "
                    f"yakalanabiliyor: {location}. 🎣"
                )

            elif (
                "saat" in question
                or "hangi saat" in question
                or "kaçta" in question
            ):

                answer = (
                    f"{fish_name} "
                    f"{time} saatleri arasında "
                    f"yakalanabiliyor. ⏰"
                )

            elif (
                "kaç altın" in question
                or "ne kadar" in question
                or "fiyat" in question
                or "satış" in question
            ):

                answer = (
                    f"{fish_name} "
                    f"{sell_price}g karşılığında satılıyor. 💰"
                )

            else:

                answer = (
                    f"{fish_name}; {season} döneminde, "
                    f"{location} bölgesinde, {time} saatleri "
                    f"arasında yakalanabiliyor ve "
                    f"{sell_price}g değerinde. 🐟"
                )

            return render_template(
                "index.html",
                answer=answer
            )


        # -------------------------
        # MAHSUL
        # -------------------------

        crop = find_crop(question)

        if crop:

            crop_name = crop["crop_tr"]
            season = crop["season"]
            growth_days = crop["growth_days"]
            sell_price = crop["sell_price"]

            if (
                "kaç günde" in question
                or "kaç gün" in question
                or "ne kadar sürede" in question
                or "yetiş" in question
                or "büyü" in question
            ):

                answer = (
                    f"{crop_name} "
                    f"{growth_days} günde yetişiyor. 🌱"
                )

            elif (
                "hangi mevsim" in question
                or "hangi mevsimde" in question
                or "mevsim" in question
            ):

                answer = (
                    f"{crop_name} "
                    f"{season} mevsiminde yetişiyor. ☀️"
                )

            elif (
                "kaç altın" in question
                or "ne kadar" in question
                or "fiyat" in question
                or "satış" in question
            ):

                answer = (
                    f"{crop_name} "
                    f"{sell_price}g karşılığında satılıyor. 💰"
                )

            else:

                answer = (
                    f"{crop_name}; {season} mevsiminde yetişiyor, "
                    f"{growth_days} günde büyüyor ve "
                    f"{sell_price}g karşılığında satılıyor. 🌱"
                )

            return render_template(
                "index.html",
                answer=answer
            )


        # -------------------------
        # KARAKTER
        # -------------------------

        row = find_character(question)

        if row is None:

            answer = (
                "Hmm, bunu veri tabanımda bulamadım. 😭 "
                "Bir karakter, ürün, balık veya maden adıyla "
                "tekrar deneyebilirsin."
            )

            return render_template(
                "index.html",
                answer=answer
            )

        character = row["character"]

        birthday = row.get("birthday", "")
        location = row.get("location", "")
        job = row.get("job", "")

        loved = row.get(
            "loved_gifts", ""
        ).split("|")

        liked = row.get(
            "liked_gifts", ""
        ).split("|")

        disliked = row.get(
            "disliked_gifts", ""
        ).split("|")

        schedule = row.get(
            "schedule", ""
        ).split("|")


        if (
            "sevmiyor" in question
            or "sevmediği" in question
            or "sevmedi" in question
            or "nefret" in question
        ):

            answer = (
                f"{character}, "
                f"{format_list(disliked)} "
                "hediyelerden pek hoşlanmıyor. 😬"
            )

        elif (
            "beğen" in question
            or "hoşlanıyor" in question
        ):

            answer = (
                f"{character} şunları beğeniyor: "
                f"{format_list(liked)}. 👍"
            )

        elif (
            "doğum" in question
            and "hediye" in question
        ):

            answer = (
                f"{character}'in doğum günü "
                f"{birthday}! 🎂 "
                f"Doğum gününde "
                f"{format_list(loved)} verebilirsin. 💜"
            )

        elif "doğum" in question:

            answer = (
                f"{character}'in doğum günü "
                f"{birthday}. 🎂"
            )

        elif (
            "nerede" in question
            or "hangi mekan" in question
            or "hangi yerde" in question
            or "bulabilirim" in question
        ):

            answer = (
                f"{character}'i genellikle "
                f"{location} tarafında bulabilirsin. 📍"
            )

        elif (
            "program" in question
            or "rutin" in question
            or "günlük" in question
        ):

            answer = (
                f"{character}'in programında "
                f"{format_list(schedule)} var. 🗓️"
            )

        elif (
            "iş" in question
            or "meslek" in question
        ):

            answer = (
                f"{character}'in işi {job}. 💼"
            )

        elif (
            "sev" in question
            or "hediye" in question
            or "favori" in question
            or "ne almalıyım" in question
            or "ne alayım" in question
        ):

            answer = (
                f"{character} en çok "
                f"{format_list(loved)} seviyor. 💜"
            )

        else:

            answer = (
                f"{character} hakkında doğum günü, "
                "hediyeler, işi veya nerede olduğu "
                "gibi şeyleri sorabilirsin! 🌱"
            )

    return render_template(
        "index.html",
        answer=answer
    )


# -------------------------
# UYGULAMAYI ÇALIŞTIR
# -------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )