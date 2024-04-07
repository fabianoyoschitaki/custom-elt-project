import subprocess
import time

# fallback docker-compose - to only run when source_postgres and destination_postgres are ready
def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    """Wait for PostgreSQL to become available."""
    retries = 0
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", host], check=True, capture_output=True, text=True
            )
            # pinging the actual database itself
            if "accepting connections" in result.stdout:
                print("Successfully connected to PostgreSQL!")
                return True
        except subprocess.CalledProcessError as e:
            print(f"Error connecting to PostgreSQL: {e}")
            retries += 1
            print(f"Retrying in {delay_seconds} seconds... (Attempt {retries} of {max_retries})")
            time.sleep(delay_seconds)
    # retries >= max_retries
    print("Max retries reached. Exiting")
    return False

# Use the function before running the ELT process
if not wait_for_postgres(host="source_postgres"):
    exit(1)

# if source_postgres is running, let's start the script
print("Starting ELT script...")

# we're going to use Pgres dump files here to initialize the database
# Configuration for the source PostgreSQL database
source_config = {
    # config from docker-compose source_db
    'dbname': 'source_postgres_db',
    'user': 'postgres',
    'password': 'source-secret',
    'host': 'source_postgres'
}

# Configuration for the destination PostgreSQL database
destination_config = {
    # config from docker-compose destination_db
    'dbname': 'destination_postgres_db',
    'user': 'postgres',
    'password': 'destination-secret',
    'host': 'destination_postgres'
}

# Use pg_dump to dump the source database to a SQL file
dump_to_source_db_command = [
    'pg_dump', 
    '-h', source_config['host'],
    '-U', source_config['user'],
    '-d', source_config['dbname'],
    '-f', 'data_dump.sql', # this means all data from the database will be dumped into this file
    '-w' # Do not prompt for password
]

# Set the PGPASSWORD environment variable to avoid password prompt
subprocess_env = dict(
    PGPASSWORD=source_config['password']
)


# Execute the dump command
subprocess.run(dump_to_source_db_command, env=subprocess_env, check=True)

# Use psql to load the dumped SQL file into the destination database
load_into_destination_db_command = [
    'psql', # psql command line tool 
    '-h', destination_config['host'],
    '-U', destination_config['user'],
    '-d', destination_config['dbname'],
    '-a', '-f', 'data_dump.sql',
]

# Set the PGPASSWORD environment variable for the destination database
subprocess_env = dict(
    PGPASSWORD=destination_config['password']
)

# Execute the load command
subprocess.run(load_into_destination_db_command, env=subprocess_env, check=True)

print("Ending ELT script...")
