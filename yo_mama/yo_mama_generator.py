# SPDX-FileCopyrightText: 2025 YoMama-as-a-Service contributors
# SPDX-License-Identifier: MPL-2.0
"""
Yo Mama Joke Generator using Google Gemini AI.

Supports multiple flavors (cybersecurity, tech, general) and configurable
meanness and nerdiness levels.
"""

import logging
import random
from typing import Literal, Optional
from google import genai

logger = logging.getLogger(__name__)


class YoMamaGenerator:
    """
    Generate Yo Mama jokes with customizable flavors and intensity levels.
    
    Supports:
    - Flavors: cybersecurity, tech, linux, general, gaming, programming
    - Meanness: 1-10 scale (1=gentle, 10=brutal)
    - Nerdiness: 1-10 scale (1=accessible, 10=extremely technical)
    """
    
    # Available joke flavors
    FLAVORS = [
        'classic',        # Traditional Yo Mama jokes (so fat, so ugly, etc.)
        'cybersecurity',
        'tech',
        'linux',
        'general',
        'gaming',
        'programming',
        'networking',
        'cloud',
        'devops',
        'database',
        'radio',          # Amateur radio / ham radio
        'thegame'         # Hidden Easter egg - You just lost The Game
    ]
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-lite"):
        """
        Initialize the Yo Mama joke generator.
        
        Args:
            api_key: Google Gemini API key
            model_name: Gemini model to use (default: gemini-2.5-flash-lite)
        """
        self.api_key = api_key
        self.model_name = model_name
        
        # Create Gemini client
        self.client = genai.Client(api_key=api_key)
        
        logger.info(f"Initialized YoMamaGenerator with model: {model_name}")
    
    def generate_joke(
        self,
        flavor: Optional[str] = None,
        meanness: int = 5,
        nerdiness: int = 5,
        target_name: Optional[str] = None
    ) -> str:
        """
        Generate a Yo Mama joke with specified parameters.
        
        Args:
            flavor: Joke flavor/theme (cybersecurity, tech, linux, etc.)
                   If None, a random flavor is selected
            meanness: How mean the joke should be (1-10)
                     1 = gentle and playful
                     5 = moderate roasting
                     10 = brutal and savage
            nerdiness: How technical/nerdy the joke should be (1-10)
                      1 = accessible to everyone
                      5 = requires basic tech knowledge
                      10 = extremely technical, insider references
            target_name: Optional custom name instead of "yo mama"
        
        Returns:
            Generated joke as a string
        """
        # Validate and normalize inputs
        if flavor and flavor.lower() not in self.FLAVORS:
            logger.warning(f"Unknown flavor '{flavor}', using random")
            flavor = None
        
        if flavor is None:
            flavor = random.choice(self.FLAVORS)
        else:
            flavor = flavor.lower()
        
        meanness = max(1, min(10, meanness))
        nerdiness = max(1, min(10, nerdiness))
        
        # Build the prompt
        prompt = self._build_prompt(flavor, meanness, nerdiness, target_name)
        
        try:
            # Generate the joke
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            joke = response.text.strip()
            
            logger.info(f"Generated {flavor} joke (M:{meanness}, N:{nerdiness})")
            return joke
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to generate joke: {e}")
            
            # Check if it's a rate limit/quota error (429)
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                rate_limit_jokes = [
                    "Yo mama hitting this API so hard, even Google told her to slow down! 🚦 (Rate limit exceeded, try again in a minute)",
                    "Yo mama's requests so thicc, the API said 'I need a break!' 💤 (Quota exceeded, please try again later)",
                    "Yo mama making so many requests, the API filed a restraining order! 🚨 (Rate limit hit, chill for a sec)",
                    "Yo mama so demanding, she exceeded her quota faster than a script kiddie with a new API key! ⚠️ (Try again in 60 seconds)",
                    "Yo mama hit that rate limit so fast, even the API was like 'Damn girl, pace yourself!' 🔥 (Quota exceeded, wait a minute)",
                    "Yo mama's API calls so excessive, Google Gemini ghosted her! 👻 (Rate limit reached, try again soon)"
                ]
                return random.choice(rate_limit_jokes)
            
            # For other errors, use fallback joke
            return self._get_fallback_joke(flavor)
    
    def _build_prompt(
        self,
        flavor: str,
        meanness: int,
        nerdiness: int,
        target_name: Optional[str]
    ) -> str:
        """Build the prompt for Gemini based on parameters."""
        
        # Define flavor-specific context
        flavor_contexts = {
            'classic': 'CLASSIC traditional Yo Mama jokes - use timeless formats like "so fat", "so ugly", "so old", "so stupid", "so poor", "so hairy", "so short", "so tall". Examples: "Yo mama so fat when she sits around the house, she sits AROUND the house", "Yo mama so fat when she got on the scale it said \'I need your weight not your phone number\'", "Yo mama so fat I took a picture of her last Christmas and it\'s still printing", "Yo mama like a race car she burns 4 rubbers a day". Keep it traditional, punchy, and non-technical.',
            'cybersecurity': 'cybersecurity, hacking, vulnerabilities, security tools like CrowdStrike, Shodan, Suricata, Wazuh, firewalls, encryption, CVEs',
            'tech': 'technology, computers, software, hardware, operating systems, IT support, tech companies',
            'linux': 'Linux, Unix, open source, command line, distros, kernel, bash, system administration, package managers',
            'general': 'everyday technology, smartphones, social media, internet, basic computing',
            'gaming': 'video games, gaming hardware, esports, game development, streaming, lag, FPS',
            'programming': 'coding, programming languages, APIs, debugging, git, IDEs, software development',
            'networking': 'networks, routers, switches, protocols, TCP/IP, DNS, load balancing, bandwidth',
            'cloud': 'cloud computing, AWS, Azure, GCP, containers, Kubernetes, serverless, microservices',
            'devops': 'DevOps, CI/CD, Docker, Jenkins, automation, infrastructure as code, monitoring',
            'database': 'databases, SQL, NoSQL, queries, indexes, normalization, database administrators',
            'radio': 'amateur radio, ham radio, frequencies, bands (HF/VHF/UHF), antennas, SWR, propagation, callsigns, morse code, repeaters, QSO, QSL cards, ARRL, FCC licenses (Technician/General/Extra), rigs, transceivers, DX, contestin',
            'thegame': 'The Game - a mind game where thinking about The Game means you lose. Create creative, funny ways to tell them they just lost The Game. Be clever and unexpected. Reference memes, internet culture, or tech concepts if appropriate.'
        }
        
        flavor_context = flavor_contexts.get(flavor, 'general technology')
        
        # Define meanness guidance
        meanness_guide = {
            1: 'extremely gentle and wholesome, just playful teasing',
            2: 'mild and friendly, very light roasting',
            3: 'gentle but with a slight edge',
            4: 'moderately playful with some bite',
            5: 'balanced roasting, noticeable but not harsh',
            6: 'firm roasting with clear jabs',
            7: 'harsh and pointed, definitely stinging',
            8: 'brutal and savage, no holding back',
            9: 'devastatingly mean, almost cruel',
            10: 'absolutely merciless and nuclear-level savage'
        }
        
        # Define nerdiness guidance
        nerdiness_guide = {
            1: 'use only basic everyday terms anyone would understand',
            2: 'use simple tech terms most people know',
            3: 'use common tech concepts',
            4: 'use moderately technical terms',
            5: 'use technical jargon that tech-savvy people know',
            6: 'use specialized technical terms',
            7: 'use insider technical references and acronyms',
            8: 'use advanced technical concepts and tools',
            9: 'use highly specialized technical knowledge',
            10: 'use extremely obscure technical references only experts would get'
        }
        
        target = target_name if target_name else "yo mama"
        
        prompt = f"""Generate a single "Yo Mama" style joke with these specifications:

THEME/FLAVOR: {flavor} - Focus on {flavor_context}

MEANNESS LEVEL: {meanness}/10 - {meanness_guide[meanness]}

NERDINESS LEVEL: {nerdiness}/10 - {nerdiness_guide[nerdiness]}

TARGET: Use "{target}" instead of "yo mama"

REQUIREMENTS:
- Start with "{target.capitalize()} so [adjective]..."
- The joke must be related to {flavor}
- Match the specified meanness and nerdiness levels precisely
- Be creative and clever
- Keep it concise (1-2 sentences max)
- Make it funny and original

EXAMPLES for reference (adjust based on parameters):

{flavor} examples:
- Yo mama so insecure, even CrowdStrike put her in Reduced Functionality Mode.
- Yo mama so exposed, Shodan sends her vulnerability reports.
- Yo mama so slow, when she tried to catch up on her emails, Outlook timed her out.

Generate ONE joke now, matching all specifications:"""

        return prompt
    
    def _get_fallback_joke(self, flavor: str) -> str:
        """Return a fallback joke if generation fails."""
        fallbacks = {
            'cybersecurity': "Yo mama so insecure, even CrowdStrike flagged her as a vulnerability.",
            'tech': "Yo mama so slow, buffering gives up and goes home.",
            'linux': "Yo mama so bloated, even apt-get couldn't remove her dependencies.",
            'general': "Yo mama so old, her password is literally 'password'.",
            'gaming': "Yo mama so laggy, ping timeout became her nickname.",
            'programming': "Yo mama so buggy, Stack Overflow created a tag just for her.",
            'radio': "Yo mama so noisy, she causes interference on all bands at once - 73!",
            'thegame': "Congratulations! You just lost The Game. And so did everyone reading this. Sorry not sorry. 🎮💀",
        }
        return fallbacks.get(flavor, "Yo mama so outdated, even legacy systems moved on.")
    
    def generate_batch(
        self,
        count: int = 5,
        flavor: Optional[str] = None,
        meanness: int = 5,
        nerdiness: int = 5,
        target_name: Optional[str] = None
    ) -> list[str]:
        """
        Generate multiple jokes at once.
        
        Args:
            count: Number of jokes to generate
            flavor: Joke flavor (random if None)
            meanness: Meanness level (1-10)
            nerdiness: Nerdiness level (1-10)
            target_name: Optional custom target name
            
        Returns:
            List of generated jokes
        """
        jokes = []
        for i in range(count):
            try:
                joke = self.generate_joke(
                    flavor=flavor,
                    meanness=meanness,
                    nerdiness=nerdiness,
                    target_name=target_name
                )
                jokes.append(joke)
            except Exception as e:
                logger.error(f"Failed to generate joke {i+1}/{count}: {e}")
        
        return jokes
    
    def random_joke(self) -> str:
        """Generate a completely random joke with random parameters."""
        flavor = random.choice(self.FLAVORS)
        meanness = random.randint(3, 7)  # Moderate range
        nerdiness = random.randint(3, 7)  # Moderate range
        
        return self.generate_joke(
            flavor=flavor,
            meanness=meanness,
            nerdiness=nerdiness
        )
    
    @staticmethod
    def list_flavors() -> list[str]:
        """Get list of available joke flavors."""
        return YoMamaGenerator.FLAVORS.copy()
