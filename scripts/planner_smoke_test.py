import sys
from config.logging_config import get_logger
from agent.planner import create_search_plan

logger = get_logger(__name__)

def main():
    # Default queries if none provided
    queries = sys.argv[1:] if len(sys.argv) > 1 else [
        "How do I sand the finish off this dresser?",
        "How to caulk around bathroom sink fixtures?", 
        "How can I install this projector on ceiling",        
        #"How do I refinish hardwood floors?",
        #"Best way to repair drywall holes",
        #"How can I get the scratch out of this wood table?",
        #"Fix sticky drawer",
        #"How to hang floating shelves",
    ]
    
    logger.info(f"Running planner smoke test with {len(queries)} queries")
    
    for query in queries:
        logger.info(f"Testing query: {query}")
        try:
            plan = create_search_plan(query)
            logger.debug(f"Search terms: {plan.search_terms}")
            logger.debug(f"Subreddits: {plan.subreddits}")
            logger.debug(f"Notes: {plan.notes}")
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
    
    logger.info("Smoke test complete")

if __name__ == "__main__":
    main()