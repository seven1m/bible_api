using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using System.Text.Json;
using BibleImporter.Configuration;
using BibleImporter.Services;

namespace BibleImporter;

public class Program
{
    public static async Task<int> Main(string[] args)
    {
        try
        {
            // Build configuration
            var config = BuildConfiguration();
            
            // Setup dependency injection
            var serviceProvider = ConfigureServices(config);
            
            // Get the main application service
            var app = serviceProvider.GetRequiredService<BibleImporterApp>();
            
            // Run the application
            return await app.RunAsync();
        }
        catch (Exception ex)
        {
            // Output error in required JSON format
            var error = new { error = $"Application startup failed: {ex.Message}" };
            Console.WriteLine(JsonSerializer.Serialize(error));
            return 1;
        }
    }

    private static IConfiguration BuildConfiguration()
    {
        var builder = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("config.json", optional: true, reloadOnChange: false)
            .AddIniFile("config.ini", optional: true, reloadOnChange: false)
            .AddEnvironmentVariables();

        return builder.Build();
    }

    private static ServiceProvider ConfigureServices(IConfiguration configuration)
    {
        var services = new ServiceCollection();

        // Configure logging (suppress console output except errors)
        services.AddLogging(builder =>
        {
            builder.AddConsole(options =>
            {
                options.LogToStandardErrorThreshold = LogLevel.Error;
            });
            builder.SetMinimumLevel(LogLevel.Warning);
        });

        // Bind configuration
        var config = new ImporterConfig();
        configuration.Bind(config);
        services.AddSingleton(config);

        // Register services
        services.AddScoped<BlobStorageService>();
        services.AddScoped<XmlParsingService>();
        services.AddScoped<DatabaseService>();
        services.AddScoped<BibleImporterApp>();

        return services.BuildServiceProvider();
    }
}
