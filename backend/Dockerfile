FROM perl:5.34-slim

WORKDIR /app

# Install system dependencies required for building DBD::MariaDB
# (libmariadb-dev is still correct, as DBD::MariaDB also uses it)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libmariadb-dev \
        mariadb-client \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN cpanm --notest --no-man-pages Mojolicious DBI DBD::MariaDB JSON Mojolicious::Plugin::CORS

# Copy ONLY the Perl application file
COPY app.pl ./

# The 'public' directory (for React static files) will be mounted as a volume
RUN mkdir -p /app/public

EXPOSE 8080

CMD ["hypnotoad", "-f", "app.pl"]
