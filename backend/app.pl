#!/usr/bin/env perl
use Mojolicious::Lite;
use DBI;
use JSON;

use Mojolicious::Plugin::CORS;
plugin CORS => {
  origins => ['*'],             # Allows requests from ANY origin. For development, this is fine.
                                # For production, you should replace '*' with your frontend's exact URL,
                                # e.g., 'http://localhost:8081' or 'https://your-f1-dashboard.com'
  methods => ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], # Specify allowed HTTP methods
  headers => ['Content-Type', 'Authorization'], # Specify allowed request headers
  credentials => 1, # Set to 1 if your frontend needs to send cookies or HTTP authentication credentials
  max_age => 3600, # How long preflight (OPTIONS) requests can be cached (in seconds)
};


# Explicitly set the listening port for Hypnotoad
app->config(listen => ['http://*:8080']); # <--- THIS LINE IS KEY

# MySQL connection details from environment variables
my $mysql_host = $ENV{MYSQL_HOST} || 'localhost';
my $mysql_user = $ENV{MYSQL_USER} || 'root';
my $mysql_password = $ENV{MYSQL_PASSWORD} || 'password';
my $mysql_database = $ENV{MYSQL_DATABASE} || 'f1_data';

my $dbh;
sub db_connect {
    unless ($dbh && $dbh->ping) {
        $dbh = DBI->connect(
            "DBI:MariaDB:database=$mysql_database;host=$mysql_host",
            $mysql_user,
            $mysql_password,
            { RaiseError => 1, AutoCommit => 1 }
        ) or die "Failed to connect to database: $DBI::errstr";
    }
    return $dbh;
}


# Serve static files from the 'public' directory (where your React app will be built)
app->static->paths(['./public']);
app->log->level('info');

# API endpoint to get sessions
get '/api/sessions' => sub {
    my $c = shift;
    my $dbh = db_connect();
    my $sth = $dbh->prepare("SELECT session_id, year, gp_name, session_type, date, round_number FROM sessions ORDER BY date DESC");
    $sth->execute();
    my @sessions;
    while (my $row = $sth->fetchrow_hashref) {
        push @sessions, { %$row, date => "$row->{date}" };
    }
    $c->render(json => \@sessions);
};

# API endpoint to get laps for a specific session
get '/api/laps/:session_id' => sub {
    my $c = shift;
    my $session_id = $c->param('session_id');
    unless (defined $session_id && $session_id =~ /^\d+$/) {
        $c->render(json => { error => 'Invalid session_id' }, status => 400);
        return;
    }

    my $dbh = db_connect();
    my $sth = $dbh->prepare(
        "SELECT lap_id, driver, lap_number, lap_time_ms, sector1_time_ms, sector2_time_ms, sector3_time_ms, speed_trap_kmh, tyre_compound
         FROM laps WHERE session_id = ? ORDER BY lap_number ASC, driver ASC"
    );
    $sth->execute($session_id);
    my @laps;
    while (my $row = $sth->fetchrow_hashref) {
        push @laps, $row;
    }
    $c->render(json => \@laps);
};

app->start;
