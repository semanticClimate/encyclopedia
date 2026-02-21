"""
Large encyclopedia fixture generator (500-1000 entries).

Creates a large encyclopedia for performance testing and edge cases.
Uses caching to avoid recreating encyclopedias on every test run.
Note: This fixture may take significant time to create due to Wikipedia lookups.
"""

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from Examples.create_encyclopedia_from_wordlist import create_encyclopedia_from_wordlist
from test.encyclopedia.fixtures.cache import (
    load_cached_encyclopedia,
    save_encyclopedia_to_cache
)


# Large set of terms across multiple domains
# This is a representative sample - in practice, you might generate more programmatically
LARGE_ENCYCLOPEDIA_TERMS = [
    # Climate science (50 entries)
    "climate change", "global warming", "greenhouse gas", "carbon dioxide", "methane",
    "nitrous oxide", "ozone", "aerosol", "ice sheet", "glacier", "sea level rise",
    "ocean acidification", "atmosphere", "troposphere", "stratosphere", "precipitation",
    "evaporation", "condensation", "humidity", "temperature", "weather", "climate",
    "El Niño", "La Niña", "monsoon", "hurricane", "typhoon", "tornado", "drought",
    "flood", "wildfire", "heat wave", "cold snap", "frost", "snow", "rain",
    "hail", "sleet", "fog", "cloud", "wind", "pressure", "barometer", "thermometer",
    "climate model", "IPCC", "carbon cycle", "water cycle", "albedo", "radiative forcing",
    
    # Biology (50 entries)
    "DNA", "RNA", "protein", "enzyme", "cell", "nucleus", "mitochondria", "chloroplast",
    "membrane", "chromosome", "gene", "genetics", "evolution", "natural selection",
    "mutation", "species", "ecosystem", "biodiversity", "habitat", "niche", "food chain",
    "photosynthesis", "respiration", "metabolism", "digestion", "circulation", "nervous system",
    "brain", "neuron", "muscle", "bone", "skin", "organ", "tissue", "bacteria", "virus",
    "fungus", "plant", "animal", "mammal", "bird", "fish", "reptile", "amphibian",
    "insect", "vertebrate", "invertebrate", "microorganism", "bacteria", "archaea",
    
    # Chemistry (50 entries)
    "atom", "molecule", "element", "compound", "ion", "electron", "proton", "neutron",
    "periodic table", "chemical bond", "covalent bond", "ionic bond", "hydrogen bond",
    "reaction", "catalyst", "equilibrium", "acid", "base", "pH", "salt", "solution",
    "solvent", "solute", "concentration", "molarity", "mole", "molecular weight",
    "organic chemistry", "inorganic chemistry", "biochemistry", "polymer", "monomer",
    "oxidation", "reduction", "redox", "combustion", "synthesis", "decomposition",
    "precipitation", "filtration", "distillation", "chromatography", "spectroscopy",
    "mass spectrometry", "nuclear magnetic resonance", "infrared", "ultraviolet",
    
    # Physics (50 entries)
    "force", "energy", "work", "power", "momentum", "velocity", "acceleration", "gravity",
    "mass", "weight", "density", "pressure", "volume", "temperature", "heat", "light",
    "wave", "frequency", "wavelength", "amplitude", "sound", "electricity", "magnetism",
    "electric field", "magnetic field", "current", "voltage", "resistance", "circuit",
    "semiconductor", "transistor", "diode", "capacitor", "inductor", "quantum mechanics",
    "relativity", "photon", "electron", "proton", "neutron", "nucleus", "atom",
    "molecule", "solid", "liquid", "gas", "plasma", "phase transition", "entropy",
    
    # Technology (50 entries)
    "computer", "algorithm", "software", "hardware", "programming", "code", "data",
    "database", "network", "internet", "server", "client", "protocol", "API", "web",
    "HTML", "CSS", "JavaScript", "Python", "Java", "C++", "machine learning",
    "artificial intelligence", "neural network", "deep learning", "data science",
    "big data", "cloud computing", "cybersecurity", "encryption", "blockchain",
    "cryptocurrency", "bitcoin", "smartphone", "tablet", "laptop", "desktop",
    "operating system", "Linux", "Windows", "macOS", "browser", "email", "social media",
    "search engine", "e-commerce", "online", "digital", "virtual", "augmented reality",
    
    # Geography (50 entries)
    "continent", "ocean", "sea", "lake", "river", "stream", "mountain", "hill", "valley",
    "plateau", "plain", "desert", "forest", "jungle", "tundra", "grassland", "savanna",
    "island", "peninsula", "isthmus", "cape", "bay", "gulf", "strait", "channel",
    "volcano", "earthquake", "tsunami", "erosion", "deposition", "weathering",
    "latitude", "longitude", "equator", "prime meridian", "tropic", "arctic", "antarctic",
    "hemisphere", "time zone", "climate zone", "biome", "ecosystem", "watershed",
    "drainage basin", "delta", "estuary", "fjord", "canyon", "cave",
    
    # History (50 entries)
    "civilization", "empire", "kingdom", "republic", "democracy", "monarchy", "revolution",
    "war", "peace", "treaty", "alliance", "colony", "independence", "constitution",
    "government", "politics", "election", "president", "prime minister", "parliament",
    "congress", "senate", "house", "law", "court", "judge", "jury", "trial",
    "ancient", "medieval", "renaissance", "enlightenment", "industrial revolution",
    "world war", "cold war", "renaissance", "reformation", "crusade", "exploration",
    "colonization", "slavery", "abolition", "suffrage", "civil rights", "human rights",
    "democracy", "freedom", "liberty", "justice", "equality",
    
    # Mathematics (50 entries)
    "number", "integer", "fraction", "decimal", "percentage", "ratio", "proportion",
    "algebra", "geometry", "calculus", "statistics", "probability", "equation",
    "inequality", "function", "variable", "constant", "coefficient", "exponent",
    "logarithm", "trigonometry", "sine", "cosine", "tangent", "derivative", "integral",
    "limit", "series", "sequence", "matrix", "vector", "scalar", "tensor",
    "graph", "set", "subset", "union", "intersection", "complement", "permutation",
    "combination", "factorial", "prime number", "composite number", "divisor",
    "multiple", "factor", "greatest common divisor", "least common multiple",
    
    # Medicine (50 entries)
    "disease", "illness", "symptom", "diagnosis", "treatment", "therapy", "medicine",
    "drug", "vaccine", "antibiotic", "surgery", "operation", "anesthesia", "patient",
    "doctor", "nurse", "hospital", "clinic", "pharmacy", "prescription", "dose",
    "side effect", "infection", "bacteria", "virus", "pathogen", "immune system",
    "antibody", "antigen", "vaccination", "immunization", "epidemic", "pandemic",
    "public health", "epidemiology", "prevention", "cure", "recovery", "rehabilitation",
    "mental health", "psychology", "psychiatry", "neurology", "cardiology", "oncology",
    "pediatrics", "geriatrics", "anatomy", "physiology", "pathology",
    
    # Astronomy (50 entries)
    "star", "planet", "moon", "sun", "solar system", "galaxy", "universe", "cosmos",
    "asteroid", "comet", "meteor", "meteorite", "nebula", "black hole", "neutron star",
    "white dwarf", "red giant", "supernova", "constellation", "orbit", "rotation",
    "revolution", "eclipse", "solar eclipse", "lunar eclipse", "telescope", "observatory",
    "astronaut", "spacecraft", "satellite", "space station", "space exploration",
    "Mars", "Venus", "Jupiter", "Saturn", "Mercury", "Neptune", "Uranus", "Pluto",
    "Milky Way", "Andromeda", "Big Bang", "dark matter", "dark energy", "cosmic radiation",
    "light year", "parsec", "astronomical unit", "gravity", "relativity"
]


def create_large_encyclopedia(
    add_wikipedia: bool = True,
    add_images: bool = False,  # Default False due to time constraints
    validate: bool = False,
    verbose: bool = False,
    use_cache: bool = True
) -> AmiEncyclopedia:
    """
    Create large encyclopedia for performance tests.
    
    Uses caching to avoid recreating encyclopedias on every test run.
    Cache is especially important for large encyclopedias due to creation time.
    
    Args:
        add_wikipedia: If True, add Wikipedia descriptions (default: True)
        add_images: If True, add images from Wikipedia (default: False for speed)
        validate: If True, validate results (default: False for speed)
        verbose: If True, show detailed progress (default: False)
        use_cache: If True, use cached version if available (default: True)
        
    Returns:
        AmiEncyclopedia instance with 500-1000 entries
        
    Note:
        This fixture may take significant time to create due to Wikipedia lookups.
        Consider using add_images=False for faster test execution.
        Caching is highly recommended for large encyclopedias.
    """
    title = "Large Test Encyclopedia"
    
    # Try to load from cache
    if use_cache:
        cached = load_cached_encyclopedia(
            terms=LARGE_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title
        )
        if cached is not None:
            if verbose:
                print(f"Loaded large encyclopedia from cache ({len(cached.entries)} entries)")
            return cached
    
    # Create new encyclopedia
    if verbose:
        print("Creating new large encyclopedia (this may take a very long time)...")
    
    encyclopedia = create_encyclopedia_from_wordlist(
        terms=LARGE_ENCYCLOPEDIA_TERMS,
        title=title,
        add_wikipedia=add_wikipedia,
        add_images=add_images,
        batch_size=50,
        validate=validate,
        verbose=verbose
    )
    
    # Save to cache and temp directory
    if use_cache:
        cache_file = save_encyclopedia_to_cache(
            encyclopedia=encyclopedia,
            terms=LARGE_ENCYCLOPEDIA_TERMS,
            add_wikipedia=add_wikipedia,
            add_images=add_images,
            title=title,
            save_to_temp=True
        )
        if verbose:
            print(f"Saved large encyclopedia to cache: {cache_file}")
            from test.encyclopedia.fixtures.cache import TEMP_FIXTURES_DIR
            temp_file = TEMP_FIXTURES_DIR / "large_test_encyclopedia.html"
            print(f"Saved readable copy to temp: {temp_file}")
    
    return encyclopedia
