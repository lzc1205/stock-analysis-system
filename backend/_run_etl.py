from app.utils.logger import logger

logger.info("=" * 50)
logger.info("补跑 ETL: DWD -> DWS 和 DWS -> ADS")
logger.info("=" * 50)

logger.info("Step 1: 运行 DWD -> DWS ETL...")
from etl.dwd_to_dws import run_dwd_to_dws
run_dwd_to_dws()

logger.info("Step 2: 运行 DWS -> ADS ETL...")
from etl.dws_to_ads import run_dws_to_ads
run_dws_to_ads()

logger.info("=" * 50)
logger.info("ETL 补跑完成!")
logger.info("=" * 50)