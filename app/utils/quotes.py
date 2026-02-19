"""
Motivational quotes utility.
Returns a different quote each day based on the current date.
"""
from datetime import datetime

# Pool of motivational quotes (100+ quotes for variety)
MOTIVATIONAL_QUOTES = [
    # Perseverance & Strength
    "Keep Pushing, Never Quit.",
    "Every Step Forward Is Progress.",
    "You Are Stronger Than You Think.",
    "Small Steps Lead To Big Changes.",
    "Consistency Is The Key To Success.",
    "Your Only Limit Is You.",
    "Believe In Your Journey.",
    "Progress, Not Perfection.",
    "Transform One Day At A Time.",
    "You've Got This!",

    # Wellness & Health
    "Your Health Is Your Wealth.",
    "Invest In Yourself Daily.",
    "Nourish Your Body, Feed Your Soul.",
    "Strong Body, Strong Mind.",
    "Take Care Of Yourself First.",
    "Wellness Is A Journey, Not A Destination.",
    "Your Body Hears Everything Your Mind Says.",
    "Choose Progress Over Perfection.",
    "Health Is The Real Wealth.",
    "Self-Care Isn't Selfish.",

    # Motivation & Goals
    "Dream Big, Work Hard, Stay Focused.",
    "Success Is Built Daily, Not Overnight.",
    "Make Today Count.",
    "The Best Time To Start Was Yesterday. The Next Best Time Is Now.",
    "You're Capable Of Amazing Things.",
    "Turn Your Dreams Into Plans.",
    "Every Day Is A Fresh Start.",
    "Focus On Progress, Not Perfection.",
    "Your Future Self Will Thank You.",
    "Stay Committed To Your Goals.",

    # Transformation & Growth
    "Transformation Starts Within.",
    "Glow From The Inside Out.",
    "Become The Best Version Of Yourself.",
    "Change Your Habits, Change Your Life.",
    "Growth Happens Outside Your Comfort Zone.",
    "You're Not Where You Were Yesterday.",
    "Embrace The Journey Of Becoming.",
    "Small Changes Lead To Big Results.",
    "Your Transformation Is Unique.",
    "Celebrate Every Milestone.",

    # Positivity & Mindset
    "Positive Mind, Positive Vibes, Positive Life.",
    "Your Attitude Determines Your Direction.",
    "Choose Joy Every Single Day.",
    "Radiate Confidence From Within.",
    "Be Your Own Biggest Cheerleader.",
    "You're Doing Better Than You Think.",
    "Stay Positive, Work Hard, Make It Happen.",
    "Good Things Take Time.",
    "Trust The Process.",
    "You Are Enough, Just As You Are.",

    # Discipline & Consistency
    "Discipline Is Choosing Between What You Want Now And What You Want Most.",
    "Show Up Every Day, Even When It's Hard.",
    "Consistency Beats Intensity.",
    "Small Daily Improvements Lead To Stunning Results.",
    "Success Is The Sum Of Small Efforts Repeated Daily.",
    "Don't Stop Until You're Proud.",
    "Be Stronger Than Your Excuses.",
    "Action Is The Foundational Key To All Success.",
    "The Only Bad Workout Is The One That Didn't Happen.",
    "Make Your Future Self Proud.",

    # Beauty & Self-Care
    "Glowing Skin Is Always In.",
    "Beauty Begins The Moment You Decide To Be Yourself.",
    "Self-Care Is How You Take Your Power Back.",
    "Invest In Your Skin, It's Going To Represent You For A Long Time.",
    "Confidence Is The Best Outfit.",
    "Take Time To Make Your Soul Happy.",
    "You're Beautiful Inside And Out.",
    "Treat Yourself Like Someone You Love.",
    "Skincare Is Healthcare.",
    "Love The Skin You're In.",

    # Fitness & Strength
    "Strong Is The New Beautiful.",
    "Sweat Today, Smile Tomorrow.",
    "Fitness Is Not About Being Better Than Someone Else. It's About Being Better Than You Used To Be.",
    "The Body Achieves What The Mind Believes.",
    "Push Yourself Because No One Else Is Going To Do It For You.",
    "Your Body Can Stand Almost Anything. It's Your Mind You Have To Convince.",
    "Don't Wish For It, Work For It.",
    "Sore Today, Strong Tomorrow.",
    "The Difference Between Try And Triumph Is A Little Umph.",
    "Train Like A Beast, Look Like A Beauty.",

    # Nutrition & Diet
    "You Are What You Eat, So Don't Be Fast, Cheap, Easy, Or Fake.",
    "Eat Well, Live Well, Be Well.",
    "Fuel Your Body With Good Food.",
    "Good Nutrition Creates Health In All Areas Of Our Existence.",
    "Let Food Be Thy Medicine.",
    "Eat Clean, Stay Fit, And Have A Burger To Stay Sane.",
    "Healthy Eating Is A Way Of Life.",
    "Your Diet Is A Bank Account. Good Food Choices Are Good Investments.",
    "Nourish To Flourish.",
    "Eat Better, Feel Better.",

    # Personal Development
    "The Only Person You Should Try To Be Better Than Is The Person You Were Yesterday.",
    "Work On Yourself More Than You Do On Your Job.",
    "Personal Growth Is Not A Matter Of Learning New Information But Unlearning Old Limits.",
    "Invest In Yourself. You Can Afford It. Trust Me.",
    "Level Up Your Life.",
    "Become So Confident In Who You Are That No One's Opinion Matters.",
    "Be The Change You Wish To See.",
    "Your Vibe Attracts Your Tribe.",
    "Grow Through What You Go Through.",
    "Never Stop Learning, Never Stop Growing.",

    # Inspiration
    "You Didn't Come This Far To Only Come This Far.",
    "The Comeback Is Always Stronger Than The Setback.",
    "Fall Seven Times, Stand Up Eight.",
    "Your Potential Is Endless.",
    "You're Writing Your Own Story. Make It A Good One.",
    "Stars Can't Shine Without Darkness.",
    "Difficult Roads Often Lead To Beautiful Destinations.",
    "You're Braver Than You Believe, Stronger Than You Seem, And Smarter Than You Think.",
    "This Too Shall Pass.",
    "Keep Going. You're Closer Than You Think.",
]


def get_daily_quote() -> str:
    """
    Get a motivational quote that changes daily.

    Uses the current date to select a quote from the pool,
    ensuring the same quote is shown for the entire day.

    Returns:
        Motivational quote string
    """
    # Get current date (year + day of year)
    # This ensures the quote changes daily but stays the same throughout the day
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday  # 1-366

    # Use modulo to cycle through quotes
    quote_index = day_of_year % len(MOTIVATIONAL_QUOTES)

    return MOTIVATIONAL_QUOTES[quote_index]

