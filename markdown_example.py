from printer_utils import ThermalPrinter

# Initialize printer
printer = ThermalPrinter()

markdown_text = """
# Cleopatra VII: Last Queen of Ancient Egypt

The story of Cleopatra, the last active ruler of the Ptolemaic Kingdom of Egypt, is one of political genius, cultural sophistication, and ultimately, tragic endings. Born in 69 BCE, she would become one of history's most fascinating figures, though separating fact from legend remains a constant challenge for historians.

![Bust of Cleopatra](https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Kleopatra-VII.-Altes-Museum-Berlin1.jpg/800px-Kleopatra-VII.-Altes-Museum-Berlin1.jpg)

## Early Life and Rise to Power

Growing up in Alexandria's royal palace, young Cleopatra received an extraordinary education that set her apart from her predecessors. Unlike previous Ptolemaic rulers, she mastered not only Greek but also Egyptian, demonstrating a deep respect for the culture she would govern. By the time she ascended to the throne as co-ruler with her younger brother Ptolemy XIII in 51 BCE, she had mastered an impressive array of languages and disciplines:

* Languages: Greek, Egyptian, Ethiopian, Hebrew, Arabic, Syrian, Median, Parthian, and Latin
* Studies: Philosophy, astronomy, economics, and military strategy

The path to sole rulership proved treacherous. Civil war erupted between Cleopatra and her brother, forcing her into exile. Her fortunes changed dramatically in 48 BCE when Julius Caesar arrived in Alexandria, leading to one of history's most famous political alliances.

## Key Moments in Cleopatra's Reign

**48-44 BCE: The Caesar Years**
During this period, Cleopatra secured her position through a combination of political acumen and personal charm. Her alliance with Caesar produced a son, Caesarion, and restored her to Egypt's throne. When Caesar was assassinated in 44 BCE, she faced perhaps her greatest political challenge yet.

**41-31 BCE: Alliance with Mark Antony**
Following Caesar's death, Cleopatra navigated the shifting political landscape by forming a new alliance with Mark Antony. Their relationship evolved beyond political convenience, producing three children:

* The twins Alexander Helios and Cleopatra Selene (40 BCE)
* Ptolemy Philadelphus (36 BCE)

![Hieroglyphs](https://www.egypttoday.com/siteimages/Larg/202305010115561556.jpg)

## Cultural and Economic Achievements

As ruler, Cleopatra proved herself a capable administrator. Under her guidance, Egypt experienced:

* Stabilization of the currency
* Improved agricultural production
* Strengthened international trade networks
* Renaissance in learning and scholarship at Alexandria

She maintained Egypt's independence through careful diplomacy and economic management, even as Rome's influence in the region grew increasingly dominant.

## The Final Chapter

The end came with the conflict between Octavian and Mark Antony. After their decisive defeat at the Battle of Actium in 31 BCE, events moved swiftly toward their tragic conclusion:

1. Retreat to Alexandria
2. Failed negotiations with Octavian
3. Antony's suicide
4. Cleopatra's own death in 30 BCE

![Art of Cleopatra](https://images.squarespace-cdn.com/content/v1/5a6e162f64b05f4a0d859674/1528056083829-2HPDVNEAP8CC83O73KAL/cleopatra.gif.png)

## Legacy and Historical Impact

Cleopatra's death marked not just the end of her reign but of several major historical epochs:

* The Ptolemaic Dynasty (305-30 BCE)
* Ancient Egypt's independence
* The Hellenistic Age in the Mediterranean

Yet her influence extends far beyond these endings. Modern scholarship continues to reveal a more nuanced picture of Cleopatra as a learned ruler, skilled diplomat, and capable administrator. Archaeological evidence, including coins bearing her image and contemporary papyrus documents, helps separate historical fact from Roman propaganda and later romantic embellishments.

Today, we can appreciate Cleopatra as a complex historical figure who masterfully balanced traditional Egyptian sovereignty with Hellenistic culture and Roman political reality. Her reign represents both the height of Ptolemaic achievement and its final chapter, closing three centuries of Greek rule in Egypt and thousands of years of pharaonic tradition.

Through careful study of primary sources and archaeological evidence, we continue to discover that the historical Cleopatra surpasses even the dramatic legends that have grown around her. She remains a powerful symbol of female leadership, intellectual achievement, and cultural sophistication, her story as captivating now as it was two millennia ago.
"""

printer.print_markdown(markdown_text)
printer.cut_paper() 